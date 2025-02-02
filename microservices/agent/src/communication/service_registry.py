import os

class ServiceRegistry:
    def __init__(self):
        self.services = {
            "generative-base": os.getenv("GENERATIVE_BASE_URL", "http://generative-base:8000"),
            "content-generator": "http://content-service:5000",
            "image-processor": "http://image-service:3000"
        }
    
    def get_service_endpoint(self, service_name: str) -> str:
        if service_name not in self.services:
            raise ServiceNotFoundError(f"Service {service_name} not registered")
        return self.services[service_name]

registry.register_service(
    name="generative-base",
    url=os.getenv("GENERATIVE_BASE_URL", "http://generative-base:8000")
) 