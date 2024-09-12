import os
import sys
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'L_and_R.settings')

        # If only the executable is passed, append 'runserver' as the default command
        if len(sys.argv) == 1:
            sys.argv += ['runserver']  # Default to run the development server

        # Pass the command-line arguments (without 'manage.py')
        execute_from_command_line(sys.argv)

    except Exception as e:
        print(f"Error: {e}")

    input("Press Enter to exit...")
