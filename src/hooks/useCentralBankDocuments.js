import { useState, useEffect } from 'react';
// Import JSON as a module - bundled with the app during build
// This works in both development and production when properly bundled by Vite
import centralBankDocumentsData from '../data/central-bank-documents.json';

const fallbackDocuments = {
  version: "1.0.0",
  lastUpdated: null,
  documents: []
};

export const useCentralBankDocuments = () => {
  const [documents, setDocuments] = useState(fallbackDocuments);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // First, try to use the imported JSON data (bundled with app during build)
        // This works in both development and production when Vite bundles it correctly
        if (centralBankDocumentsData && centralBankDocumentsData.documents && Array.isArray(centralBankDocumentsData.documents)) {
          setDocuments(centralBankDocumentsData);
          console.log(`✅ Loaded ${centralBankDocumentsData.documents.length} central bank documents from bundled data`);
          setLoading(false);
          return;
        }
        
        // Fallback: If imported data is not available, try fetching from public path
        // This handles edge cases where the import might fail
        const fallbackPaths = [
          '/central-bank-documents.json',
          './central-bank-documents.json'
        ];
        
        let fetchError = null;
        for (const path of fallbackPaths) {
          try {
            const response = await fetch(path);
            if (response.ok) {
              const data = await response.json();
              if (data && data.documents && Array.isArray(data.documents)) {
                setDocuments(data);
                console.log(`✅ Loaded ${data.documents.length} central bank documents from ${path}`);
                setLoading(false);
                return;
              }
            }
          } catch (err) {
            fetchError = err;
            continue;
          }
        }
        
        // If all methods fail, throw an error
        throw new Error('Failed to load central bank documents: Import failed and all fetch paths failed');
        
      } catch (err) {
        console.error('❌ Error loading central bank documents:', err);
        setError(err.message);
        setDocuments(fallbackDocuments);
      } finally {
        setLoading(false);
      }
    };

    loadDocuments();
  }, []);

  const refreshDocuments = async () => {
    setLoading(true);
    try {
      // Try to reload from imported data first
      if (centralBankDocumentsData && centralBankDocumentsData.documents && Array.isArray(centralBankDocumentsData.documents)) {
        setDocuments(centralBankDocumentsData);
        setLoading(false);
        return;
      }
      
      // Fallback to fetch
      const response = await fetch('/central-bank-documents.json');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('❌ Error refreshing documents:', err);
    } finally {
      setLoading(false);
    }
  };

  return {
    documents: documents.documents || [],
    lastUpdated: documents.lastUpdated,
    loading,
    error,
    refresh: refreshDocuments
  };
};

