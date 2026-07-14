import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import {
  AnalyzeTaskResponse,
  CriteriaScore,
  HistoryItem,
  ResumeAnalysisResponse,
  TaskStatus,
  analyzeResume,
  getExportUrl,
  getHistory,
  getTaskStatus
} from './api';

const statusLabels: Record<TaskStatus, string> = {
  pending: 'В очереди',
  started: 'Анализируется',
  success: 'Готово',
  failure: 'Ошибка'
};

const criteriaLabels: Record<string, string> = {
  skills: 'Навыки',
  experience: 'Опыт',
  structure: 'Структура',
  language: 'Язык'
};

function formatCriteriaName(key: string): string {
  return criteriaLabels[key] || key.replace(/_/g, ' ').replace(/^./, (value) => value.toUpperCase());
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value));
}

function getScoreLabel(score: number): string {
  if (score >= 9) return 'Отлично';
  if (score >= 7) return 'Хорошо';
  if (score >= 5) return 'Нужно усилить';
  return 'Слабое место';
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [callbackUrl, setCallbackUrl] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [cached, setCached] = useState(false);
  const [result, setResult] = useState<ResumeAnalysisResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const isPolling = Boolean(taskId && taskStatus && !['success', 'failure'].includes(taskStatus));

  const acceptedTypes = useMemo(() => ['application/pdf', 'text/plain'], []);

  async function loadHistory() {
    setIsHistoryLoading(true);
    try {
      const response = await getHistory(8, 0);
      setHistory(response.items);
      setHistoryTotal(response.total);
    } catch (loadError) {
      console.error(loadError);
    } finally {
      setIsHistoryLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (!isPolling || !taskId) return;

    const intervalId = window.setInterval(async () => {
      try {
        const response = await getTaskStatus(taskId);
        setTaskStatus(response.status);

        if (response.status === 'success' && response.result) {
          setResult(response.result);
          setError(null);
          window.clearInterval(intervalId);
          loadHistory();
        }

        if (response.status === 'failure') {
          setError('Анализ завершился с ошибкой. Проверьте worker, Redis и настройки LLM-провайдера.');
          window.clearInterval(intervalId);
        }
      } catch (pollError) {
        setError(pollError instanceof Error ? pollError.message : 'Не удалось получить статус задачи');
        window.clearInterval(intervalId);
      }
    }, 2200);

    return () => window.clearInterval(intervalId);
  }, [isPolling, taskId, taskStatus]);

  function validateFile(nextFile: File): string | null {
    const extension = nextFile.name.toLowerCase().split('.').pop();
    const isValidType = acceptedTypes.includes(nextFile.type) || extension === 'pdf' || extension === 'txt';

    if (!isValidType) {
      return 'Загрузите файл в формате PDF или TXT.';
    }

    if (nextFile.size > 5 * 1024 * 1024) {
      return 'Максимальный размер файла — 5 MB.';
    }

    return null;
  }

  function selectFile(nextFile?: File) {
    if (!nextFile) return;

    const validationError = validateFile(nextFile);
    if (validationError) {
      setError(validationError);
      return;
    }

    setFile(nextFile);
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      setError('Выберите PDF или TXT резюме для анализа.');
      return;
    }

    setIsSubmitting(true);
    setTaskId(null);
    setTaskStatus(null);
    setCached(false);
    setResult(null);
    setError(null);

    try {
      const response: AnalyzeTaskResponse = await analyzeResume(file, callbackUrl);
      setCached(response.cached);
      setTaskId(response.task_id);
      setTaskStatus(response.status);

      if (response.cached && response.result) {
        setResult(response.result);
        await loadHistory();
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось отправить резюме на анализ');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">AI Resume Analyzer</p>
          <h1>Загрузите резюме и получите понятный отчёт за пару кликов</h1>
          <p className="hero-copy">
            Фронтенд подключён к существующему FastAPI backend: отправляет файл, показывает статус Celery-задачи,
            отображает оценки, рекомендации и историю анализов.
          </p>
          <div className="hero-actions">
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="secondary-link">
              API docs
            </a>
            <button className="ghost-button" onClick={() => loadHistory()} type="button">
              Обновить историю
            </button>
          </div>
        </div>
        <div className="hero-card">
          <span className="hero-card-label">Средний результат</span>
          <strong>{result ? `${result.overall_score}/10` : '—'}</strong>
          <p>{result ? getScoreLabel(result.overall_score) : 'Загрузите файл, чтобы увидеть оценку'}</p>
        </div>
      </section>

      <section className="grid-layout">
        <form className="panel upload-panel" onSubmit={handleSubmit}>
          <div className="panel-heading">
            <span className="step-badge">1</span>
            <div>
              <h2>Загрузка резюме</h2>
              <p>Поддерживаются PDF и TXT до 5 MB.</p>
            </div>
          </div>

          <div
            className={`dropzone ${isDragging ? 'dragging' : ''}`}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              selectFile(event.dataTransfer.files[0]);
            }}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') fileInputRef.current?.click();
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,application/pdf,text/plain"
              onChange={(event) => selectFile(event.target.files?.[0])}
              hidden
            />
            <div className="upload-icon">↥</div>
            <h3>{file ? file.name : 'Перетащите файл сюда'}</h3>
            <p>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'или нажмите, чтобы выбрать файл'}</p>
          </div>

          <label className="field-label" htmlFor="callbackUrl">
            Callback URL <span>опционально</span>
          </label>
          <input
            id="callbackUrl"
            className="text-input"
            type="url"
            value={callbackUrl}
            onChange={(event) => setCallbackUrl(event.target.value)}
            placeholder="https://example.com/webhook"
          />

          {error && <div className="alert error-alert">{error}</div>}

          <button className="primary-button" disabled={isSubmitting || isPolling} type="submit">
            {isSubmitting ? 'Отправляем...' : isPolling ? 'Анализ уже запущен' : 'Запустить анализ'}
          </button>
        </form>

        <section className="panel status-panel">
          <div className="panel-heading">
            <span className="step-badge">2</span>
            <div>
              <h2>Статус анализа</h2>
              <p>Фронтенд автоматически опрашивает backend.</p>
            </div>
          </div>

          <div className="status-list">
            <StatusRow active={Boolean(taskId)} done={Boolean(taskId)} title="Файл принят" description={taskId || 'Task ID появится после отправки'} />
            <StatusRow active={taskStatus === 'pending'} done={Boolean(taskStatus && taskStatus !== 'pending')} title="Очередь Celery" description={taskStatus ? statusLabels[taskStatus] : 'Ожидание'} />
            <StatusRow active={taskStatus === 'started'} done={taskStatus === 'success'} title="AI-анализ" description="Skills, experience, structure, language" />
            <StatusRow active={taskStatus === 'success'} done={taskStatus === 'success'} title="Отчёт готов" description={cached ? 'Результат взят из Redis cache' : 'Результат сохранён в PostgreSQL'} />
          </div>

          {cached && <div className="alert success-alert">Cache HIT: повторное резюме обработано мгновенно.</div>}
        </section>
      </section>

      {result && <ResultPanel result={result} />}

      <HistoryPanel items={history} total={historyTotal} loading={isHistoryLoading} onReload={loadHistory} />
    </main>
  );
}

function StatusRow({
  active,
  done,
  title,
  description
}: {
  active: boolean;
  done: boolean;
  title: string;
  description: string;
}) {
  return (
    <div className={`status-row ${active ? 'active' : ''} ${done ? 'done' : ''}`}>
      <span className="status-dot" />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}

function ResultPanel({ result }: { result: ResumeAnalysisResponse }) {
  const criteriaEntries = Object.entries(result.criteria || {});

  return (
    <section className="panel result-panel">
      <div className="result-header">
        <div>
          <p className="eyebrow">Готовый отчёт</p>
          <h2>{result.file_name || 'Resume analysis'}</h2>
          <p>{result.summary}</p>
        </div>
        <div className="score-circle" aria-label={`Score ${result.overall_score} out of 10`}>
          <strong>{result.overall_score}</strong>
          <span>/10</span>
        </div>
      </div>

      <div className="criteria-grid">
        {criteriaEntries.map(([key, criterion]) => (
          <CriteriaCard key={key} title={formatCriteriaName(key)} criterion={criterion} />
        ))}
      </div>

      <div className="insights-grid">
        <InsightList title="Сильные стороны" items={result.top_strengths} />
        <InsightList title="Что улучшить" items={result.top_improvements} />
      </div>
    </section>
  );
}

function CriteriaCard({ title, criterion }: { title: string; criterion: CriteriaScore }) {
  return (
    <article className="criteria-card">
      <div className="criteria-topline">
        <h3>{title}</h3>
        <span>{criterion.score}/10</span>
      </div>
      <p>{criterion.feedback}</p>
      {criterion.suggestions?.length > 0 && (
        <ul>
          {criterion.suggestions.map((suggestion) => (
            <li key={suggestion}>{suggestion}</li>
          ))}
        </ul>
      )}
    </article>
  );
}

function InsightList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="insight-list">
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function HistoryPanel({
  items,
  total,
  loading,
  onReload
}: {
  items: HistoryItem[];
  total: number;
  loading: boolean;
  onReload: () => void;
}) {
  return (
    <section className="panel history-panel">
      <div className="history-heading">
        <div>
          <p className="eyebrow">История</p>
          <h2>Последние анализы</h2>
          <p>{total ? `Всего записей: ${total}` : 'Пока нет сохранённых анализов.'}</p>
        </div>
        <button className="ghost-button" onClick={onReload} type="button">
          {loading ? 'Обновляем...' : 'Обновить'}
        </button>
      </div>

      <div className="history-list">
        {items.map((item) => (
          <article className="history-item" key={item.id_}>
            <div>
              <strong>{item.file_name || `Analysis #${item.id_}`}</strong>
              <p>{item.summary}</p>
              <span>{formatDate(item.created_at)}</span>
            </div>
            <div className="history-actions">
              <span className="mini-score">{item.overall_score}/10</span>
              <a className="export-link" href={getExportUrl(item.id_)} target="_blank" rel="noreferrer">
                PDF
              </a>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default App;
