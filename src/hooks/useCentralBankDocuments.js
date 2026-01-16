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
      
      // Try multiple paths to handle different deployment scenarios
      const paths = [
        '/central-bank-documents.json',
        './central-bank-documents.json',
        '/documents/central-bank-documents.json'
      ];
      
      let response = null;
      let lastError = null;
      
      for (const path of paths) {
        try {
          response = await fetch(path, {
            cache: 'no-cache',
            headers: {
              'Accept': 'application/json'
            }
          });
          
          if (response.ok) {
            break;
          }
        } catch (err) {
          lastError = err;
          continue;
        }
      }
      
      if (!response || !response.ok) {
        throw new Error(`HTTP error! status: ${response?.status || 'unknown'}. Tried paths: ${paths.join(', ')}`);
      }
      
      const data = await response.json();
      
      if (data && data.documents && Array.isArray(data.documents)) {
        setDocuments(data);
        console.log(`✅ Loaded ${data.documents.length} central bank documents`);
      } else {
        throw new Error('Invalid data format - missing documents array');
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

