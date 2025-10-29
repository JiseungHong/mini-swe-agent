"""
Utilities for working with SWE-bench_Pro instances.

Based on https://github.com/scaleapi/SWE-bench_Pro-os/blob/main/helper_code/image_uri.py
"""


def get_swebench_pro_docker_image(instance: dict, dockerhub_username: str = "jefzda") -> str:
    """
    Generate the Docker Hub image URI for a SWE-bench_Pro instance.

    Args:
        instance: SWE-bench_Pro instance dict with 'instance_id' and 'repo' fields
        dockerhub_username: Docker Hub username (default: "jefzda")

    Returns:
        Full Docker image URI (e.g., "jefzda/sweap-images:tag")
    """
    uid = instance["instance_id"]
    repo_name = instance["repo"]

    repo_base, repo_name_only = repo_name.lower().split("/")
    hsh = uid.replace("instance_", "")

    # Handle special cases from the original script
    if uid == "instance_element-hq__element-web-ec0f940ef0e8e3b61078f145f34dc40d1938e6c5-vnan":
        repo_name_only = "element-web"
    elif "element-hq" in repo_name.lower() and "element-web" in repo_name.lower():
        repo_name_only = "element"
        if hsh.endswith("-vnan"):
            hsh = hsh[:-5]
    elif hsh.endswith("-vnan"):
        hsh = hsh[:-5]

    # Construct tag
    tag = f"{repo_base}.{repo_name_only}-{hsh}"

    # Docker tags have a 128 character limit
    if len(tag) > 128:
        tag = tag[:128]

    return f"{dockerhub_username}/sweap-images:{tag}"
