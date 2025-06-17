from backend.app.core.celery_app import celery_app
import time

@celery_app.task(name="example_task_name") # You can explicitly name your task
def example_task(word: str) -> str:
    """
    A simple example task that returns a string.
    """
    # Simulate some work
    time.sleep(2)
    result = f"Example task says: {word}"
    print(f"Task {example_task.name} completed with result: {result}")
    return result

@celery_app.task
def another_example_task(x: int, y: int) -> int:
    """
    Another simple task that adds two numbers.
    """
    time.sleep(1)
    result = x + y
    print(f"Task {another_example_task.name} completed: {x} + {y} = {result}")
    return result

# To call these tasks from your FastAPI app:
# from backend.app.tasks.example_tasks import example_task
# example_task.delay("hello from FastAPI")
# result = example_task.apply_async(args=["hello with apply_async"])
# print(result.get()) # This will block until the task is finished and result is available

# For more complex scenarios, you might have a dedicated module/service to dispatch tasks.
