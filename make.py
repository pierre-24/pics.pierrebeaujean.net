import pathlib

from base_models import BaseFetcher, FileSeeker, BaseTransformer, BaseFile


class Printer(BaseTransformer):
    def __call__(self, f: BaseFile, *args, **kwargs):
        print(f.source_path)


if __name__ == '__main__':
    from settings_default import images_extensions, images_source

    fetch = BaseFetcher(
        seeker=FileSeeker(pathlib.Path(images_source), images_extensions),
        transformers=[Printer()]
    )

    list(fetch())
