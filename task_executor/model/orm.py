import enum
from typing import List
from typing import Optional
from sqlalchemy import JSON, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Status(enum.Enum):
    NEW = 'new'
    IN_PROGRESS = 'in-progress'
    COMPLETED_ERROR = 'completed-error'
    COMPLETED_OK = 'completed-ok'
    RE_PROCESS = 're-process'

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str]
    content:  Mapped[str] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(Enum(Status))
    created_at: Mapped[str]
    updated_at: Mapped[str]
    task_logs: Mapped[List["TaskLog"]] = relationship(back_populates="task")

    def __repr__(self) -> str:
        return f"""Task(id={self.id!r}, tag={self.tag!r}, content={self.content!r},
                   status={self.status!r}, created_at={self.created_at!r}, updated_at={self.updated_at!r},
                   task_logs={self.task_logs!r}"""

class TaskLog(Base):
    __tablename__ = "task_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    message:  Mapped[str]
    status: Mapped[str] = mapped_column(Enum(Status))
    created_at: Mapped[str]
    updated_at: Mapped[str]
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"))
    task: Mapped["Task"] = relationship(back_populates="task_logs")

    def __repr__(self) -> str:
        return f"""TaskLog(id={self.id!r}, message={self.message!r}, status={self.status!r},
                   created_at={self.created_at!r}, updated_at={self.updated_at!r}"""