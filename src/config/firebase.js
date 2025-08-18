// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "your_firebase_api_key_here",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "fxsentinel.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "fxsentinel",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "fxsentinel.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "92187574391",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:92187574391:web:0b232b7fe364c639434672",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-1QMRKVJD8C"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const analytics = getAnalytics(app);

export default firebaseConfig; 