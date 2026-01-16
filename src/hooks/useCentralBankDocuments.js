import { useState, useEffect } from 'react';
// Import JSON as a module - bundled with the app, no routing needed
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
    try {
      setLoading(true);
      setError(null);
      
      // Use imported JSON data directly (bundled with app during build)
      if (centralBankDocumentsData && centralBankDocumentsData.documents && Array.isArray(centralBankDocumentsData.documents)) {
        setDocuments(centralBankDocumentsData);
        console.log(`✅ Loaded ${centralBankDocumentsData.documents.length} central bank documents`);
      } else {
        throw new Error('Invalid data format - missing documents array');
      }
      
    } catch (err) {
      console.error('❌ Error loading central bank documents:', err);
      setError(err.message);
      setDocuments(fallbackDocuments);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshDocuments = () => {
    // For imported data, refresh just reloads the same data
    // In the future, this could fetch from an API endpoint if needed
    setLoading(true);
    setTimeout(() => {
      setDocuments(centralBankDocumentsData);
      setLoading(false);
    }, 100);
  };

  return {
    documents: documents.documents || [],
    lastUpdated: documents.lastUpdated,
    loading,
    error,
    refresh: refreshDocuments
  };
};

