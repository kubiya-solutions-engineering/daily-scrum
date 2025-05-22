def initialize():
    """Initialize Scrum tools and configuration."""
    try:
        print("Starting Scrum Master tools set up...")
        from .initialization import initialize as init_scrum_setup
        init_scrum_setup()
        print("Scrum Master tools initialization completed")
    except Exception as e:
        print(f"Failed to initialize Scrum Master tools: {str(e)}")
        raise

# Run initialization when module is imported
print("Loading Scrum Master tools module...")
initialize()

# Import tools after initialization
from .tools import *