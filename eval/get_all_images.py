# enable concurrent docker image pulling: https://gemini.google.com/share/0ea003825496
# this can trigger docker hub API rate limit; use pro subscription to have a higher quota
import docker
from datasets import load_dataset
from p_tqdm import p_map


def get_swebench_docker_image_name(instance: dict) -> str:
    """Get the image name for a SWEBench instance."""
    image_name = instance.get("image_name", None)
    if image_name is None:
        # Docker doesn't allow double underscore, so we replace them with a magic token
        iid = instance["instance_id"]
        id_docker_compatible = iid.replace("__", "_1776_")
        image_name = f"swebench/sweb.eval.x86_64.{id_docker_compatible}:latest".lower()
    return image_name


def pull_single_image(image_name: str):
    """Worker function to initialize its own client and pull."""
    try:
        client = docker.from_env()
        print(image_name, flush=True)
        client.images.pull(image_name)
    except Exception as e:
        print(f"Failed {image_name}: {e}")
        raise e


def pull_all_images():
    # ... your dataset loading logic ...
    dataset_path = "princeton-nlp/SWE-Bench_Verified"
    instances = list(load_dataset(dataset_path, split="test"))
    image_names = [get_swebench_docker_image_name(instance) for instance in instances]

    # Use p_map on the wrapper function that handles its own client
    p_map(pull_single_image, image_names, num_cpus=16, desc="Pulling images")


if __name__ == "__main__":
    pull_all_images()
