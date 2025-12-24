from pipeline import Pipeline, PipelineConfig
from pathlib import Path

config = PipelineConfig(
    project_dir=Path("~/projects/sysadmin").expanduser(),
    max_iterations=10,
    max_retries_per_task=3,
)

p = Pipeline(config)
p.run()
