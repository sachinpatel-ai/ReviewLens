import { useCallback, useEffect, useRef, useState } from "react";
import { errorMessage, getAnalytics, getBatches } from "../services/api";

/** Loads batches + analytics for the selected batch and polls while analysis runs. */
export default function useBatches() {
  const [batches, setBatches] = useState([]);
  const [batchId, setBatchId] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timer = useRef(null);

  const refresh = useCallback(async (preferId) => {
    try {
      const list = await getBatches();
      setBatches(list);
      const id = preferId ?? batchId ?? list[0]?.id ?? null;
      setBatchId(id);
      setAnalytics(await getAnalytics(id ?? undefined));
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, []);

  const current = batches.find((b) => b.id === batchId) || null;

  useEffect(() => {
    clearTimeout(timer.current);
    if (current?.status === "analyzing") timer.current = setTimeout(() => refresh(batchId), 2500);
    return () => clearTimeout(timer.current);
  }, [current?.status, batches, batchId, refresh]);

  const select = (id) => { setLoading(true); refresh(id); };

  return { batches, batchId, current, analytics, loading, error, refresh, select };
}
