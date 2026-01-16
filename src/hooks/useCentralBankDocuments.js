import { useState, useEffect, useCallback } from 'react';

const fallbackDocuments = {
  version: "1.0.0",
  lastUpdated: null,
  documents: []
};

export const useCentralBankDocuments = () => {
  const [documents, setDocuments] = useState(fallbackDocuments);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch from public directory (served statically)
      const response = await fetch('/central-bank-documents.json');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data && data.documents && Array.isArray(data.documents)) {
        setDocuments(data);
        console.log(`✅ Loaded ${data.documents.length} central bank documents`);
      } else {
        throw new Error('Invalid data format');
      }
      
    } catch (err) {
      console.error('❌ Error fetching central bank documents:', err);
      setError(err.message);
      // Keep existing data on error (don't clear on transient errors)
      if (documents.documents.length === 0) {
        setDocuments(fallbackDocuments);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents: documents.documents || [],
    lastUpdated: documents.lastUpdated,
    loading,
    error,
    refresh: fetchDocuments
  };
};

