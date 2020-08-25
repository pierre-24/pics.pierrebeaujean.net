from typing import Iterable
import pathlib

from base_models import BaseFetcher, FileSeeker, BaseTransformer, BaseClassifier, BaserWriter, BaseCollector, \
    BasePipeline


def make(
        images_source: pathlib.Path = pathlib.Path('pictures'),
        images_extensions: Iterable[str] = ('jpg', 'JPG', 'jpeg', 'JPEG'),
        transformers: Iterable[BaseTransformer] = (),
        classifiers: Iterable[BaseClassifier] = (),
        writers: Iterable[BaserWriter] = ()):

    # 1. Fetch (seek & transform)
    seek = FileSeeker(images_source, images_extensions)
    fetch = BaseFetcher(seeker=seek, transformers=transformers)

    # 2. Collect (classify)
    collect = BaseCollector(fetcher=fetch, classifiers=classifiers)

    # 3. Pipeline (write)
    pipeline = BasePipeline(collector=collect, writers=writers)

    # Go!
    pipeline()
