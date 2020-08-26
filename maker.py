from typing import Iterable

from base_models import BaseFetcher, BaseSeeker, BaseTransformer, BaseClassifier, BaserWriter, BaseCollector, \
    BasePipeline


def make(
        seek: BaseSeeker = BaseSeeker(),
        transformers: Iterable[BaseTransformer] = (),
        classifiers: Iterable[BaseClassifier] = (),
        writers: Iterable[BaserWriter] = ()):

    # 1. Fetch (seek & transform)
    fetch = BaseFetcher(seeker=seek, transformers=transformers)

    # 2. Collect (classify)
    collect = BaseCollector(fetcher=fetch, classifiers=classifiers)

    # 3. Pipeline (write)
    pipeline = BasePipeline(collector=collect, writers=writers)

    # Go!
    pipeline()
