from typing import Dict, List
from asyncio import Task

class TaskStore:
    # store list of tasks per user (main + subtasks)
    _tasks: Dict[int, List[Task]] = {}
    # store progress index per user to avoid resending
    _progress: Dict[int, int] = {}

    @classmethod
    def set_task(cls, user_id: int, task: Task):
        """Set the main task for user_id, cancelling any existing tasks."""
        cls.cancel_task(user_id)
        cls._tasks[user_id] = [task]

    @classmethod
    def add_subtask(cls, user_id: int, task: Task):
        """Add a subtask for the user (won't remove main task)."""
        if user_id not in cls._tasks:
            cls._tasks[user_id] = []
        cls._tasks[user_id].append(task)

    @classmethod
    def pop_and_cancel_last_subtask(cls, user_id: int):
        """Cancel and remove the last subtask for the user (keeps main task)."""
        if user_id in cls._tasks and cls._tasks[user_id]:
            # if there's only one task and it's the main task, don't pop it here
            if len(cls._tasks[user_id]) == 1:
                return
            task = cls._tasks[user_id].pop()
            try:
                if not task.done():
                    task.cancel()
            except Exception:
                pass

    @classmethod
    def cancel_task(cls, user_id: int):
        """Cancel and remove all tasks for user_id."""
        if user_id in cls._tasks:
            for task in cls._tasks[user_id]:
                try:
                    if not task.done():
                        task.cancel()
                except Exception:
                    pass
            cls._tasks.pop(user_id)
        # also clear progress when cancelling
        if user_id in cls._progress:
            cls._progress.pop(user_id)

    @classmethod
    def has_task(cls, user_id: int) -> bool:
        """Return True if there's any active (not done) task for user_id."""
        if user_id in cls._tasks:
            for task in cls._tasks[user_id]:
                try:
                    if not task.done():
                        return True
                except Exception:
                    continue
        return False

    @classmethod
    def set_progress(cls, user_id: int, index: int):
        cls._progress[user_id] = int(index)

    @classmethod
    def get_progress(cls, user_id: int) -> int:
        return int(cls._progress.get(user_id, 0))

    @classmethod
    def clear_progress(cls, user_id: int):
        if user_id in cls._progress:
            cls._progress.pop(user_id)

    @classmethod
    def finish_task(cls, user_id: int):
        """Remove stored task references for user_id without cancelling running tasks."""
        if user_id in cls._tasks:
            cls._tasks.pop(user_id)
        if user_id in cls._progress:
            cls._progress.pop(user_id)