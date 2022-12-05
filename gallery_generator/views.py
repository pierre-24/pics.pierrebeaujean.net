import pathlib
from typing import List
from jinja2 import Environment, FileSystemLoader, select_autoescape

from gallery_generator.models import Tag, Picture, Page

env = Environment(
    loader=FileSystemLoader(pathlib.Path(__file__).parent / 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


class TemplateView:
    template_name: str = None

    def __init__(self, common_context: dict):
        self.common_context = common_context

    def get_url(self) -> str:
        raise NotImplementedError()

    def get_context_data(self, **kwargs) -> dict:
        return dict(view=self, **self.common_context)

    def render(self, target: pathlib.Path, **kwargs):
        with pathlib.Path(target / self.get_url()).open('w') as f:
            template = env.get_template(self.template_name)
            f.write(template.render(**self.get_context_data(**kwargs)))


class TagView(TemplateView):
    template_name = 'tag.html'

    def __init__(self, tag: Tag, pictures: List[Picture], common_context: dict):
        super().__init__(common_context)

        self.tag = tag
        self.pictures = pictures

    def get_url(self) -> str:
        return self.tag.get_url()

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx['tag'] = self.tag
        ctx['pictures'] = self.pictures

        return ctx


class PageView(TemplateView):
    template_name = 'page.html'

    def __init__(self, page: Page, common_context: dict):
        super().__init__(common_context)
        self.page = page

    def get_url(self) -> str:
        return self.page.get_url()

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx['page'] = self.page

        return ctx


class IndexView(TemplateView):
    template_name = 'index.html'

    def __init__(self, thumbnails, common_context: dict):
        super().__init__(common_context)
        self.thumbnails = thumbnails

    def get_url(self) -> str:
        return 'index.html'

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)

        ctx['thumbnails'] = self.thumbnails

        return ctx
