from typing import Callable
import shutil
from typing import Iterable
import pathlib
from jinja2 import Environment, select_autoescape, FileSystemLoader

from mosgal.base_models import BaserWriter, Collection

env = Environment(
    loader=FileSystemLoader('./templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


class TemplateMixin:

    def __init__(self, template_name=''):
        self.template_name = template_name

    def render_template(self, **kwargs):
        template = env.get_template(self.template_name)
        return template.render(**kwargs)


class BuildDirectory(BaserWriter):
    """Create a directory for building everything (remove if exists), then move everything into ``destination``
    """

    def __init__(self, build: pathlib.Path, writers: Iterable[BaserWriter] = ()):
        super().__init__()

        self.writers = writers
        self.build = build

    def __call__(self, collections: Iterable[Collection], destination: pathlib.Path, *args, **kwargs) -> None:
        # create build directory
        if self.build.exists():
            shutil.rmtree(self.build)

        self.build.mkdir()

        # apply writers in build directory
        for write in self.writers:
            write(collections, self.build)

        # move build directory into destination
        if destination.exists():
            shutil.rmtree(destination)

        self.build.rename(destination)


class WriteTemplate(TemplateMixin, BaserWriter):
    """Write a template into ``destination``
    """

    def __init__(self, template_name, destination_file: pathlib.Path()):
        super().__init__(template_name)
        self.destination_file = destination_file

    def get_context_data(self, collections: Iterable[Collection], *args, **kwargs):
        return {}

    def __call__(self, collections: Iterable[Collection], destination: pathlib.Path, *args, **kwargs):
        with pathlib.Path.joinpath(destination, self.destination_file).open('w') as f:
            f.write(self.render_template(**self.get_context_data(collections, *args, **kwargs)))


class WriteIndex(WriteTemplate):
    def __init__(self, collections: Iterable[str], picture_attribute: str, sorting_criterion: str = None):
        super().__init__('index.html', 'index.html')
        self.collections = collections
        self.picture_attribute = picture_attribute
        self.sorting_criterion = sorting_criterion

    def get_context_data(self, collections: Iterable[Collection], *args, **kwargs):
        data = super().get_context_data(collections, *args, **kwargs)

        data['collections'] = collections
        data['featured_collections'] = {}

        for name in self.collections:
            current_collection = next(filter(lambda cl: cl.name == name, collections))
            collect = []
            for el in current_collection.elements:
                info = {
                    'name': el.name,
                    'description': el.description,
                    'picture': el.files[-1].attributes[self.picture_attribute]
                }
                if self.sorting_criterion is not None:
                    info.update({self.sorting_criterion: el.files[-1].attributes[self.sorting_criterion]})
                collect.append(info)

            if self.sorting_criterion is not None:
                collect.sort(key=lambda el: el[self.sorting_criterion])

            data['featured_collections'][name] = collect

        return data


class WriteImages(BaserWriter):
    """
    Copy (or link to, depending on ``strategy``) images (found in ``attributes``) into a ``directory``,
    based on a given collection (``base_collection``).

    ``strategy`` can either be ``copy`` or ``symlink``.

    Store the final path into ``{initial attribute name}_final``.
    """

    def __init__(
            self,
            directory: pathlib.Path,
            base_collection: str,
            attributes: Iterable[str],
            namer: Callable,
            strategy: str = 'copy'):

        super().__init__()

        self.directory = directory
        self.name = namer
        self.what = attributes
        self.strategy = strategy
        self.base_collection = base_collection

    def __call__(self, collections: Iterable[Collection], destination: pathlib.Path, *args, **kwargs):
        dest_dir = destination.joinpath(self.directory)
        dest_dir.mkdir()

        for c in collections:
            if c.name == self.base_collection:
                for e in c.elements:
                    for i in e.files:
                        for w in self.what:
                            initial_path = pathlib.Path(i.attributes[w])
                            name = self.name(i, w)

                            final_path = dest_dir.joinpath(name)
                            if self.strategy == 'copy':
                                shutil.copy(initial_path, final_path)
                            elif self.strategy == 'symlink':
                                final_path.symlink_to(initial_path.resolve())

                            i.attributes[w + '_final'] = str(self.directory.joinpath(name))
