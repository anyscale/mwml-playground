name: service-mlops
project_id: PROJECT_ID
compute_config: COMPUTE_CONFIG_NAME
build_id: CLUSTER_ENV_ID
ray_serve_config:
  import_path: deploy.services.service:entrypoint
  runtime_env:
    working_dir: .
    upload_path: UPLOAD_PATH
    env_vars:
      EXPERIMENT_NAME: llm