import os
from blar_graph.graph_construction.core.base_parser import BaseParser
from blar_graph.graph_construction.utils.tree_parser import get_function_name
import tree_sitter_languages


class PythonParser(BaseParser):
    def __init__(self):
        super().__init__("python")
        self.extensions = [".py"]

    def _remove_extensions(self, file_path):
        no_extension_path = str(file_path)
        for extension in self.extensions:
            no_extension_path = no_extension_path.replace(extension, "")
        return no_extension_path

    def is_package(self, directory):
        return os.path.exists(os.path.join(directory, "__init__.py"))

    def find_module_path(self, module_name, start_dir, project_root):
        current_dir = start_dir
        components = module_name.split(".")

        # Try to find the module by traversing up towards the root until the module path is found or root is reached
        while current_dir.startswith(project_root):
            possible_path = os.path.join(current_dir, *components)
            # Check for a direct module or package
            if os.path.exists(possible_path + ".py") or self.is_package(possible_path):
                return possible_path.replace("/", ".")
            # Move one directory up
            current_dir = os.path.dirname(current_dir)
        return None

    def resolve_relative_import_path(self, import_statement, current_file_path, project_root):
        if import_statement.startswith(".."):
            import_statement = import_statement[2:]
            current_file_path = os.sep.join(current_file_path.split(os.sep)[:-1])
        elif import_statement.startswith("."):
            import_statement = import_statement[1:]
        else:
            return self.find_module_path(import_statement, current_file_path, project_root)

        return self.resolve_relative_import_path(import_statement, current_file_path, project_root)

    def resolve_import_path(self, import_statement, current_file_directory, project_root):
        """
        Resolve the absolute path of an import statement.
        import_statement: The imported module as a string (e.g., 'os', 'my_package.my_module').
        current_file_directory: The directory of the file containing the import statement.
        project_root: The root directory of the project.
        """
        # Handling relative imports
        if import_statement.startswith("."):
            current_file_directory = os.sep.join(current_file_directory.split(os.sep)[:-1])
            return self.resolve_relative_import_path(import_statement, current_file_directory, project_root)
        else:
            # Handling absolute imports
            return self.find_module_path(import_statement, current_file_directory, project_root)

    def parse_function_call(self, func_call: str, inclusive_scopes) -> tuple[str, int]:
        func_name = get_function_name(func_call)

        if func_name:
            if "self." in func_name:
                for parent in reversed(inclusive_scopes[:-1]):
                    if parent["type"] == "class_definition":
                        func_name = func_name.replace("self.", parent["name"] + ".")
                        break

            return func_name

        return None

    def skip_directory(self, directory: str) -> bool:
        return directory == "__pycache__"

    def parse_file(
        self,
        file_path: str,
        root_path: str,
        directory_path: str,
        visited_nodes: dict,
        global_imports: dict,
    ):
        if file_path.endswith("__init__.py"):
            return [], [], self.parse_init(file_path, root_path)
        return self.parse(file_path, root_path, directory_path, visited_nodes, global_imports)

    def parse_init(self, file_path: str, root_path: str):
        parser = tree_sitter_languages.get_parser(self.language)
        with open(file_path, "r") as file:
            code = file.read()
        tree = parser.parse(bytes(code, "utf-8"))
        imports = {}
        for node in tree.root_node.children:
            if node.type == "import_from_statement":
                import_statements = node.named_children

                from_statement = import_statements[0]
                from_text = from_statement.text.decode()
                for import_statement in import_statements[1:]:
                    import_path = self.resolve_import_path(from_text, file_path, root_path)
                    new_import_path = import_path + "." + import_statement.text.decode()
                    import_alias = ".".join(file_path.split(os.sep)[:-1]) + "." + import_statement.text.decode()
                    imports[import_alias] = new_import_path

        return imports
