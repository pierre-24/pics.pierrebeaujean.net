from base_models import BaseTransformer, BaseFile
from maker import make


class Printer(BaseTransformer):
    def __call__(self, f: BaseFile, *args, **kwargs):
        print(f.source_path)


if __name__ == '__main__':
    make(transformers=[Printer()])
