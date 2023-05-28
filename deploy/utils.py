import subprocess
import tempfile

import boto3
import typer
import yaml
from anyscale import AnyscaleSDK

# Initialize
app = typer.Typer()
sdk = AnyscaleSDK()


@app.command()
def get_project_id(
    project_name: str = typer.Option(..., "--project-name", "-n", help="name of the Anyscale project")
) -> str:
    """Get the project id."""
    output = subprocess.run(
        ["anyscale", "project", "list", "--name=" + project_name, "--created-by-me"], capture_output=True, text=True
    ).stdout
    lines = output.split("\n")
    matching_lines = [line for line in lines if project_name in line]
    last_line = matching_lines[-1] if matching_lines else None
    project_id = last_line.split()[0]
    return project_id


@app.command()
def get_latest_cluster_env_build_id(
    cluster_env_name: str = typer.Option(..., "--cluster-env-name", "-n", help="name of the cluster environment")
) -> str:
    """Get the latest cluster environment build id."""
    res = sdk.search_cluster_environments({"name": {"equals": cluster_env_name}})
    apt_id = res.results[0].id
    res = sdk.list_cluster_environment_builds(apt_id)
    bld_id = res.results[-1].id
    return bld_id


@app.command()
def submit_job(
    yaml_config_fp: str = typer.Option(..., "--yaml-config-fp", help="path of the job's yaml config file"),
    cluster_env_name: str = typer.Option(..., "--cluster-env-name", help="cluster environment's name"),
    run_id: str = typer.Option("", "--run-id", help="run ID to use to execute ML workflow"),
    commit_id: str = typer.Option("default", "--commit-id", help="used as UUID to store results to S3"),
) -> None:
    """Submit a job to Anyscale."""
    # Load yaml config
    with open(yaml_config_fp, "r") as file:
        yaml_config = yaml.safe_load(file)

    # Edit yaml config
    yaml_config["build_id"] = get_latest_cluster_env_build_id(cluster_env_name=cluster_env_name)
    yaml_config["runtime_env"]["env_vars"]["run_id"] = run_id
    yaml_config["runtime_env"]["env_vars"]["commit_id"] = commit_id

    # Execute Anyscale job
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=True, mode="w+b") as temp_file:
        temp_file_path = temp_file.name
        yaml.dump(yaml_config, temp_file, encoding="utf-8")
        subprocess.run(["anyscale", "job", "submit", "--wait", temp_file_path])


@app.command()
def save_to_s3(
    file_path: str = typer.Option(..., "--file-path", "-fp", help="path of file to save to S3"),
    bucket_name: str = typer.Option(..., "--bucket-name", help="name of S3 bucket (without s3:// prefix)"),
    bucket_path: str = typer.Option(..., "--bucket-path", help="path in S3 bucket to save to"),
) -> None:
    """Save file to S3 bucket."""
    s3 = boto3.client("s3")
    s3.upload_file(file_path, bucket_name, bucket_path)


if __name__ == "__main__":
    app()