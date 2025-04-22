"""
Debug utilities for development and testing.
"""
import os
import logging
from typing import List, Dict, Any
import importlib.util
import questionary


class DebugTools:
    """
    A class for navigating and running example files.
    """

    def __init__(self):
        """Initialize debug tools."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Configure console handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def get_example_files(self) -> Dict[str, Any]:
        """
        Get tree structure of example files and converters.

        Returns:
            Dictionary representing the file tree
        """
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        src_dir = os.path.join(project_root, 'src')
        tree = {}

        def build_tree(path: str) -> Dict[str, Any]:
            tree = {}
            try:
                for item in os.listdir(path):
                    # Skip __pycache__ directories
                    if item == "__pycache__":
                        continue

                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        subtree = build_tree(full_path)
                        # Only add non-empty directories
                        if subtree:
                            tree[item] = subtree
                    elif item.endswith('.py'):
                        tree[item] = full_path
            except FileNotFoundError:
                pass
            return tree

        # tree = build_tree('src')

        # Add all Python files from the converters directories
        for module_name in os.listdir(src_dir):
            module_path = os.path.join(src_dir, module_name)

            # Skip non-directories and special directories
            if not os.path.isdir(module_path) or module_name.startswith('__'):
                continue

            # Check for converters directory in this module
            converters_path = os.path.join(module_path)
            if os.path.isdir(converters_path):
                converters_tree = build_tree(converters_path)
                tree[module_name] = converters_tree

        return tree

    def create_choices(self, tree: Dict[str, Any], prefix: str = "", level: int = 0) -> List[questionary.Choice]:
        """
        Create questionary choices from tree structure.

        Args:
            tree: File tree dictionary
            prefix: Path prefix for nested items
            level: Current nesting level

        Returns:
            List of questionary choices
        """
        choices = []
        indent = "  " * level
        is_last = True

        # Sort items to show directories first, then files
        items = sorted(tree.items(), key=lambda x: (not isinstance(x[1], dict), x[0]))

        for i, (name, value) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "

            if isinstance(value, dict):
                # Directory
                choices.append(questionary.Choice(
                    title=f"{indent}{connector}📁 {name}/",
                    value=f"dir:{prefix}{name}",
                    description=f"Browse directory: {name}"
                ))
                choices.extend(self.create_choices(value, f"{prefix}{name}/", level + 1))
            else:
                # File
                choices.append(questionary.Choice(
                    title=f"{indent}{connector}📄 {name}",
                    value=f"file:{value}",
                    description=f"Run example: {name}"
                ))

        # Add back option for nested directories
        if prefix:
            choices.append(questionary.Choice(
                title=f"{indent}└── 🔙 ..",
                value="back",
                description="Go back"
            ))

        return choices

    def run_example_file(self, file_path: str) -> None:
        """
        Run a Python file (example or converter).

        Args:
            file_path: Path to the Python file
        """
        file_name = os.path.basename(file_path)
        file_type = "example" if "/examples/" in file_path else "converter" if "/converters/" in file_path else "file"

        self.logger.info(f"\nRunning {file_type}: {file_name}")
        self.logger.info("=" * 80)

        try:
            spec = importlib.util.spec_from_file_location("module", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, 'main'):
                    self.logger.info("Found main() function, executing...")
                    module.main()
                else:
                    self.logger.info("No main() function found, module was imported successfully.")

                    # Show module attributes as a simple help
                    public_attrs = [attr for attr in dir(module) if not attr.startswith('_')]
                    if public_attrs:
                        self.logger.info("\nAvailable public attributes/functions:")
                        for attr in sorted(public_attrs):
                            if callable(getattr(module, attr)):
                                self.logger.info(f"  - {attr}() [function]")
                            else:
                                self.logger.info(f"  - {attr} [variable]")
        except Exception as e:
            self.logger.error(f"Error running {file_type}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def show_menu(self) -> None:
        """Show interactive menu for browsing and running examples."""
        current_path = []
        current_root = None  # Tracks which root directory we're in (examples, converters, etc.)

        while True:
            # Get full tree
            tree = self.get_example_files()

            # Handle root level display
            if not current_root:
                # At root level, show all available root directories
                choices = []

                # Sort to show directories in a consistent order
                root_dirs = sorted(tree.keys())

                for i, dir_name in enumerate(root_dirs):
                    is_last = i == len(root_dirs) - 1
                    connector = "└── " if is_last else "├── "

                    choices.append(questionary.Choice(
                        title=f"{connector}📁 {dir_name}/",
                        value=f"root:{dir_name}",
                        description=f"Browse {dir_name} directory"
                    ))

                # Add exit option
                choices.append(questionary.Choice(
                    title="❌ Exit",
                    value="exit",
                    description="Exit debug menu"
                ))

                # Show current location
                self.logger.info(f"\n📂 Root")
                self.logger.info("=" * 80)

                # Show menu
                answer = questionary.select(
                    "Select a category to browse:",
                    choices=choices
                ).ask()

                if answer is None or answer == "exit":
                    break

                if answer.startswith("root:"):
                    current_root = answer[5:]
                    continue
            else:
                # Navigate within a specific root directory
                # Start from the root directory
                subtree = tree[current_root]

                # Navigate to current path
                for path in current_path:
                    subtree = subtree[path]

                # Create choices for current level
                choices = self.create_choices(subtree, "/".join(current_path) + "/" if current_path else "")

                # Add back option if we're in a subdirectory
                if not current_path:
                    choices.append(questionary.Choice(
                        title="🔙 Back to Root",
                        value="root",
                        description="Go back to main categories"
                    ))

                # Add exit option
                choices.append(questionary.Choice(
                    title="❌ Exit",
                    value="exit",
                    description="Exit debug menu"
                ))

                # Show current path
                if current_path:
                    current_location = f"📂 {current_root}/{'/'.join(current_path)}"
                else:
                    current_location = f"📂 {current_root}"

                self.logger.info(f"\n{current_location}")
                self.logger.info("=" * 80)

                # Show menu
                answer = questionary.select(
                    f"Select an item from {current_root}:",
                    choices=choices
                ).ask()

                if answer is None:
                    self.logger.info("No answer provided. Exiting...")
                    break

                if answer == "exit":
                    break
                elif answer == "root":
                    current_root = None
                    current_path = []
                    continue
                elif answer == "back":
                    current_path.pop()
                    continue
                elif answer.startswith("dir:"):
                    # Navigate into directory
                    dir_name = answer[4:].split("/")[-1].rstrip("/")
                    current_path.append(dir_name)
                    continue
                elif answer.startswith("file:"):
                    # Run example file
                    file_path = answer[5:]
                    self.run_example_file(file_path)
                    input("\nPress Enter to continue...")


def main():
    """Main entry point for the debug menu."""
    debug = DebugTools()
    debug.show_menu()


if __name__ == "__main__":
    main()
