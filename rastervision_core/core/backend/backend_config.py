from typing import Optional, List, TYPE_CHECKING

from rastervision.pipeline.config import Config, register_config

if TYPE_CHECKING:
    from rastervision.core.rv_pipeline.rv_pipeline import RVPipeline  # noqa
    from rastervision.core.backend.backend import Backend  # noqa


@register_config('backend')
class BackendConfig(Config):
    """Configure a :class:`.Backend`."""

    def build(self, pipeline: 'RVPipeline', tmp_dir: str) -> 'Backend':
        raise NotImplementedError()

    def get_bundle_filenames(self) -> List[str]:
        """Returns the names of files that should be included in a model bundle.

        The files are assumed to be in the train/ directory generated by the train
        command. Note that only the names, not the full paths should be returned.
        """
        raise NotImplementedError()

    def update(self, pipeline: Optional['RVPipeline'] = None):  # noqa
        pass

    def filter_commands(self, commands: List[str]) -> List[str]:
        """Filter out any commands that are not needed or supported."""
        return commands