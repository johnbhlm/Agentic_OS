import os
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class PromptManager:
    """
    用于管理并渲染基于 Jinja2 的 Prompt 模板。
    模板应定义在 templates_path 指定的目录中，
    并在配置中通过模板 key 指定文件名。
    """

    def __init__(self, config: dict):
        """
        :param config: 字典，包含模板路径与模板映射表：
                       {
                         "templates_path": "/path/to/templates",
                         "templates": {
                             "llm_planner": "planner_prompt.j2",
                             "rag_query": "rag_prompt.j2"
                         }
                       }
        """
        self.templates_path = config.get("templates_path", "")
        self.template_map = config.get("templates", {})
        self.env = Environment(
            loader=FileSystemLoader(self.templates_path),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def _load_template(sefl,key:str):
        pass

    def render(self, key: str, **kwargs) -> str:
        """
        渲染指定模板

        :param key: 模板 key（例如 "llm_planner"）
        :param kwargs: 渲染参数
        :return: 渲染后的字符串
        """
        if key not in self.template_map:
            raise ValueError(f"Prompt template key '{key}' not found in configuration.")
        tmpl_file = self.template_map[key]
        try:
            template = self.env.get_template(tmpl_file)
            return template.render(**kwargs)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template file '{tmpl_file}' not found in {self.templates_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to render template '{key}': {e}")
        
    def render_ymal(self,key:str,**kwargs) ->str:
        if key not in self.template_map:
            raise ValueError(f"Prompt template key '{key}' not found in configuration.")
        tmpl_file = self.template_map[key]
        try:
            with open(self.templates_path+tmpl_file, "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)

            return prompt_yaml
        except TemplateNotFound:
            raise FileNotFoundError(f"Template file '{tmpl_file}' not found in {self.templates_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to render template '{key}': {e}")
        

