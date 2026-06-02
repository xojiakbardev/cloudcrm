"""Manage API instances via the Docker Engine API.

Uses Docker Compose's own labels so scaled containers are indistinguishable
from ones started with `docker compose up --scale api=N`.
"""
import threading
from typing import List

import docker

from app.config import settings

_lock = threading.Lock()


class DockerManager:
    def __init__(self):
        self.client = docker.from_env()

    # ---- discovery ----
    def _container_filter(self):
        return {
            "label": [
                f"com.docker.compose.project={settings.compose_project}",
                f"com.docker.compose.service={settings.api_service}",
            ]
        }

    def list_api_containers(self) -> List[dict]:
        containers = self.client.containers.list(
            all=True, filters=self._container_filter()
        )
        result = []
        for c in containers:
            try:
                result.append(
                    {
                        "id": c.id[:12],
                        "name": c.name,
                        "status": c.status,
                        "number": int(
                            c.labels.get("com.docker.compose.container-number", "0")
                        ),
                    }
                )
            except docker.errors.NotFound:
                # Container vanished between list and read — skip it.
                continue
        return sorted(result, key=lambda x: x["number"])

    def current_count(self) -> int:
        return len(
            [c for c in self.list_api_containers() if c["status"] == "running"]
        )

    # ---- helpers for creating/removing replicas ----
    def _next_number(self, containers) -> int:
        used = {c["number"] for c in containers}
        n = 1
        while n in used:
            n += 1
        return n

    def _reference_container(self):
        """Pick an existing API container to clone config (image/env/network)."""
        containers = self.client.containers.list(
            all=True, filters=self._container_filter()
        )
        return containers[0] if containers else None

    def scale_to(self, target: int) -> dict:
        """Scale the API service to `target`, clamped to [min, max]."""
        with _lock:
            target = max(settings.min_instances, min(settings.max_instances, target))
            containers = self.list_api_containers()
            running = [c for c in containers if c["status"] == "running"]
            current = len(running)

            if target > current:
                self._scale_up(target - current, containers)
            elif target < current:
                self._scale_down(current - target, running)

            return {
                "previous": current,
                "target": target,
                "current": self.current_count(),
            }

    def _scale_up(self, n: int, existing):
        ref = self._reference_container()
        if ref is None:
            raise RuntimeError("No reference API container found to clone from")

        attrs = ref.attrs
        image = attrs["Config"]["Image"]
        # Clone env but drop per-container vars so each new replica gets its own
        # identity (INSTANCE_ID defaults to the container hostname).
        env = [
            e for e in attrs["Config"]["Env"]
            if not e.startswith("HOSTNAME=") and not e.startswith("INSTANCE_ID=")
        ]
        labels = dict(attrs["Config"]["Labels"])
        networks = list(attrs["NetworkSettings"]["Networks"].keys())
        primary_net = networks[0] if networks else settings.api_network

        nums = [c["number"] for c in existing]
        api = self.client.api
        for _ in range(n):
            num = 1
            while num in nums:
                num += 1
            nums.append(num)

            labels["com.docker.compose.container-number"] = str(num)
            name = f"{settings.compose_project}-{settings.api_service}-{num}"

            # IMPORTANT: attach the service-name alias ('api') so Docker's
            # embedded DNS includes this container when Nginx resolves
            # `api:8000`. Without the alias the load balancer never sees it.
            networking_config = api.create_networking_config(
                {
                    primary_net: api.create_endpoint_config(
                        aliases=[settings.api_service]
                    )
                }
            )
            host_config = api.create_host_config(
                restart_policy={"Name": "unless-stopped"}
            )
            resp = api.create_container(
                image,
                environment=env,
                labels=labels,
                name=name,
                host_config=host_config,
                networking_config=networking_config,
            )
            container_id = resp["Id"]
            api.start(container_id)

            # Attach any remaining networks (also with the service alias).
            for net_name in networks[1:]:
                try:
                    self.client.networks.get(net_name).connect(
                        container_id, aliases=[settings.api_service]
                    )
                except docker.errors.APIError:
                    pass

    def _scale_down(self, n: int, running):
        # Remove the highest-numbered containers first (keep #1 stable).
        victims = sorted(running, key=lambda x: x["number"], reverse=True)[:n]
        for v in victims:
            try:
                c = self.client.containers.get(v["name"])
                c.stop(timeout=5)
                c.remove(force=True)
            except docker.errors.NotFound:
                pass

    def remove_container(self, name: str) -> bool:
        with _lock:
            # Never drop below the minimum.
            if self.current_count() <= settings.min_instances:
                return False
            try:
                c = self.client.containers.get(name)
                c.stop(timeout=5)
                c.remove(force=True)
                return True
            except docker.errors.NotFound:
                return False


manager = DockerManager()
