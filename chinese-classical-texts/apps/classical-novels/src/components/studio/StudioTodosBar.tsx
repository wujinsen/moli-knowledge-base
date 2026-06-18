import { useCallback, useEffect, useState } from 'react';
import { fetchStudioTodos } from '../../lib/studio/client';
import type { BookSlug, StudioTodo, StudioTodosReport } from '../../lib/studio/types';

export type AutoSendPayload = {
  text: string;
  intent?: StudioTodo['kind'];
};

type Props = {
  bookSlug: BookSlug;
  onTodo: (todo: StudioTodo) => void;
};

export default function StudioTodosBar({ bookSlug, onTodo }: Props) {
  const [report, setReport] = useState<StudioTodosReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStudioTodos(bookSlug);
      setReport(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [bookSlug]);

  useEffect(() => {
    load();
  }, [load]);

  const todos = report?.todos ?? [];
  const warnCount = todos.filter((t) => t.severity === 'warn').length;

  if (!loading && !error && todos.length === 0) {
    return null;
  }

  return (
    <div className="studio-todos">
      <button
        type="button"
        className="studio-todos-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        待办
        {todos.length > 0 && (
          <span className={`studio-todos-badge${warnCount ? ' studio-todos-badge-warn' : ''}`}>
            {todos.length}
          </span>
        )}
        {loading && <span className="studio-todos-loading">…</span>}
      </button>

      {error && <span className="studio-todos-error">{error}</span>}

      {open && todos.length > 0 && (
        <ul className="studio-todos-list">
          {todos.map((todo) => (
            <li key={todo.id}>
              <button
                type="button"
                className={`studio-todos-item studio-todos-item--${todo.severity}`}
                onClick={() => {
                  onTodo(todo);
                  setOpen(false);
                }}
              >
                <span className="studio-todos-kind">/{todo.kind.replace('_', ' ')}</span>
                <span className="studio-todos-msg">{todo.message}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {open && (
        <button type="button" className="studio-todos-refresh" disabled={loading} onClick={load}>
          刷新
        </button>
      )}
    </div>
  );
}
