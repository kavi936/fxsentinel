// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCeyOao-K-cU6ah3fhAQ_K6WWEl5ijBDMI",
  authDomain: "fxsentinel.firebaseapp.com",
  projectId: "fxsentinel",
  storageBucket: "fxsentinel.firebasestorage.app",
  messagingSenderId: "92187574391",
  appId: "1:92187574391:web:0b232b7fe364c639434672",
  measurementId: "G-1QMRKVJD8C"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const analytics = getAnalytics(app);

export default firebaseConfig; 