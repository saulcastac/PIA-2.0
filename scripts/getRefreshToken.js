import { google } from 'googleapis';
import readline from 'readline';
import dotenv from 'dotenv';

dotenv.config();

const oauth2Client = new google.auth.OAuth2(
  process.env.GOOGLE_CALENDAR_CLIENT_ID,
  process.env.GOOGLE_CALENDAR_CLIENT_SECRET,
  process.env.GOOGLE_CALENDAR_REDIRECT_URI || 'http://localhost:3000/auth/callback'
);

const scopes = ['https://www.googleapis.com/auth/calendar'];

const authUrl = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  scope: scopes,
  prompt: 'consent', // Fuerza a mostrar el consentimiento para obtener refresh token
});

console.log('\n========================================');
console.log('OBTENER REFRESH TOKEN DE GOOGLE CALENDAR');
console.log('========================================\n');
console.log('1. Abre esta URL en tu navegador:');
console.log('\n' + authUrl + '\n');
console.log('2. Autoriza la aplicación');
console.log('3. Copia el código de autorización de la URL de redirección\n');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question('Ingresa el código de autorización: ', async (code) => {
  try {
    const { tokens } = await oauth2Client.getToken(code);
    
    console.log('\n========================================');
    console.log('✅ TOKENS OBTENIDOS');
    console.log('========================================\n');
    console.log('Access Token:', tokens.access_token);
    console.log('\n🔑 REFRESH TOKEN (guarda este valor):');
    console.log(tokens.refresh_token);
    console.log('\nAgrega este refresh token a tu archivo .env:');
    console.log(`GOOGLE_CALENDAR_REFRESH_TOKEN=${tokens.refresh_token}\n`);
    
    rl.close();
  } catch (error) {
    console.error('\n❌ Error obteniendo token:', error.message);
    rl.close();
    process.exit(1);
  }
});

