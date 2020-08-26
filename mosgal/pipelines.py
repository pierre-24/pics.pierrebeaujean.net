from typing import Iterable

from mosgal.base_models import BaseFetcher, BaseSeeker, BaseTransformer, BaseClassifier, BaserWriter, BaseCollector, \
    BasePublisher


def simple_pipeline(
        seek: BaseSeeker = BaseSeeker(),
        transformers: Iterable[BaseTransformer] = (),
        classifiers: Iterable[BaseClassifier] = (),
        writers: Iterable[BaserWriter] = ()):

    # 1. Fetch (seek & transform)
    fetch = BaseFetcher(seeker=seek, transformers=transformers)

    # 2. Collect (classify)
    collect = BaseCollector(fetcher=fetch, classifiers=classifiers)

    # 3. Publish (write)
    publish = BasePublisher(collector=collect, writers=writers)

    # Go!
    return publish
