from typing import Iterable, Callable

import pathlib

from mosgal.base_models import BaseFetcher, BaseSeeker, BaseTransformer, BaseClassifier, BaserWriter, BaseCollector, \
    BaseCharacterizer, BasePublisher


def simple_pipeline(
        destination: pathlib.Path,
        seek: BaseSeeker = BaseSeeker(),
        transformers: Iterable[BaseTransformer] = (),
        organizer: Callable = lambda li: li,
        classifiers: Iterable[BaseClassifier] = (),
        characterizers: Iterable[BaseCharacterizer] = (),
        writers: Iterable[BaserWriter] = (),):

    # 1. Fetch (seek & transform)
    fetch = BaseFetcher(seeker=seek, transformers=transformers)

    # 2. Collect (classify)
    collect = BaseCollector(fetcher=fetch, classifiers=classifiers, organizer=organizer, characterizers=characterizers)

    # 3. Publish (write)
    publish = BasePublisher(destination, collector=collect, writers=writers)

    # Go!
    return publish
