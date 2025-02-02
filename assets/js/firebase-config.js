// firebase-config.js

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-auth-domain.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-storage-bucket.appspot.com",
    messagingSenderId: "your-messaging-sender-id",
    appId: "your-app-id"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get Auth instance
const auth = firebase.auth();

export { auth };
