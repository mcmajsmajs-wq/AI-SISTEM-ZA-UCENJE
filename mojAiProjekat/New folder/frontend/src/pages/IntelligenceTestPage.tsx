/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * IntelligenceTestPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { intelligenceTestApi } from '@/services/api'
import toast from 'react-hot-toast'
import { 
  Brain, 
  ChevronRight, 
  ChevronLeft, 
  Trophy,
  RefreshCw,
  Settings,
  Plus,
  Minus
} from 'lucide-react'
import clsx from 'clsx'

type QuestionType = 'spatial' | 'logical' | 'numerical' | 'verbal' | 'general' | 'flags'

interface Question {
  id: number
  type: QuestionType
  question: string
  options: string[]
  correctAnswer: number
  timeLimit: number
  image?: string
  countryCode?: string
}

interface CategoryConfig {
  spatial: number
  logical: number
  numerical: number
  verbal: number
  general: number
  flags: number
}

const FLAG_CDN_URL = 'https://flagcdn.com/w320'

const getCountryCode = (emoji: string): string => {
  const emojiToCode: Record<string, string> = {
    '🇨🇳': 'cn', '🇺🇸': 'us', '🇬🇧': 'gb', '🇫🇷': 'fr', '🇩🇪': 'de',
    '🇮🇹': 'it', '🇪🇸': 'es', '🇷🇺': 'ru', '🇯🇵': 'jp', '🇰🇷': 'kr',
    '🇨🇦': 'ca', '🇦🇺': 'au', '🇧🇷': 'br', '🇮🇳': 'in', '🇵🇰': 'pk',
    '🇹🇷': 'tr', '🇸🇦': 'sa', '🇦🇪': 'ae', '🇮🇱': 'il', '🇨🇭': 'ch',
    '🇦🇹': 'at', '🇧🇪': 'be', '🇳🇱': 'nl', '🇵🇱': 'pl', '🇸🇪': 'se',
    '🇳🇴': 'no', '🇩🇰': 'dk', '🇫🇮': 'fi', '🇬🇷': 'gr', '🇵🇹': 'pt',
    '🇮🇪': 'ie', '🇦🇷': 'ar', '🇨🇴': 'co', '🇨🇱': 'cl', '🇵🇪': 'pe',
    '🇲🇽': 'mx', '🇻🇪': 've', '🇪🇬': 'eg', '🇿🇦': 'za', '🇳🇬': 'ng',
    '🇰🇪': 'ke', '🇲🇦': 'ma', '🇩🇿': 'dz', '🇹🇳': 'tn', '🇮🇷': 'ir',
    '🇮🇶': 'iq', '🇸🇾': 'sy', '🇯🇴': 'jo', '🇱🇧': 'lb', '🇦🇲': 'am',
    '🇦🇿': 'az', '🇬🇪': 'ge', '🇺🇦': 'ua', '🇧🇾': 'by', '🇲🇩': 'md',
    '🇷🇴': 'ro', '🇧🇬': 'bg', '🇷🇸': 'rs', '🇲🇪': 'me', '🇭🇷': 'hr',
    '🇸🇮': 'si', '🇲🇰': 'mk', '🇦🇱': 'al', '🇨🇿': 'cz', '🇸🇰': 'sk',
    '🇭🇺': 'hu', '🇱🇹': 'lt', '🇱🇻': 'lv', '🇪🇪': 'ee', '🇳🇿': 'nz',
    '🇵🇭': 'ph', '🇮🇩': 'id', '🇲🇾': 'my', '🇸🇬': 'sg', '🇹🇭': 'th',
    '🇻🇳': 'vn', '🇰🇭': 'kh', '🇱🇦': 'la', '🇲🇲': 'mm', '🇧🇩': 'bd',
    '🇳🇵': 'np', '🇧🇹': 'bt', '🇱🇰': 'lk', '🇲🇻': 'mv', '🇲🇴': 'mo',
    '🇭🇰': 'hk', '🇹🇼': 'tw', '🇰🇵': 'kp', '🇲🇳': 'mn', '🇰🇿': 'kz',
    '🇺🇿': 'uz', '🇹🇯': 'tj', '🇹🇲': 'tm', '🇰🇬': 'kg', '🇦🇫': 'af',
    '🇶🇦': 'qa', '🇰🇼': 'kw', '🇧🇭': 'bh', '🇴🇲': 'om', '🇧🇳': 'bn',
    '🇲🇱': 'my', '🇸🇩': 'sd', '🇪🇹': 'et', '🇹🇿': 'tz', '🇺🇬': 'ug',
    '🇿🇼': 'zw', '🇿🇲': 'zm', '🇲🇿': 'mz', '🇦🇴': 'ao', '🇳🇦': 'na',
    '🇧🇼': 'bw', '🇱🇸': 'ls', '🇸🇿': 'sz', '🇷🇼': 'rw', '🇧🇮': 'bi',
    '🇲🇼': 'mw', '🇲🇬': 'mg', '🇸🇨': 'sc', '🇲🇺': 'mu', '🇨🇻': 'cv',
    '🇬🇲': 'gm', '🇬🇭': 'gh', '🇸🇱': 'sl', '🇱🇷': 'lr', '🇨🇮': 'ci',
    '🇸🇳': 'sn', '🇬🇳': 'gn', '🇬🇼': 'gw', '🇸🇴': 'so', '🇩🇯': 'dj',
  }
  return emojiToCode[emoji] || ''
}

const getFlagUrl = (image: string | undefined, countryCode: string | undefined): string => {
  if (countryCode) {
    return `${FLAG_CDN_URL}/${countryCode}.png`
  }
  if (image) {
    const code = getCountryCode(image)
    if (code) {
      return `${FLAG_CDN_URL}/${code}.png`
    }
  }
  return ''
}

const ALL_QUESTIONS: Question[] = [
  // SPATIAL - 85 questions
  { id: 1, type: 'spatial', question: 'Koji odgovarajući kubus nastaje kada se savije mreža?', options: ['Kubus A', 'Kubus B', 'Kubus C', 'Nijedan'], correctAnswer: 0, timeLimit: 45 },
  { id: 2, type: 'spatial', question: 'Koja figura je simetrična osi označenoj linijom?', options: ['Figura A', 'Figura B', 'Figura C', 'Nijedna'], correctAnswer: 1, timeLimit: 30 },
  { id: 3, type: 'spatial', question: 'Koji je sledeći oblik u nizu: ⬜ ▢ △ ○ ⬜ ?', options: ['△', '○', '▢', '⬜'], correctAnswer: 0, timeLimit: 25 },
  { id: 4, type: 'spatial', question: 'Koji je rezultat rotacije figure za 90° u smeru kazaljke na sat?', options: ['➡️', '⬇️', '⬅️', '⬆️'], correctAnswer: 0, timeLimit: 20 },
  { id: 5, type: 'spatial', question: 'Koja je zgrada identična nakon rotacije od 180°?', options: ['A i C', 'B i D', 'Samo A', 'Nijedna'], correctAnswer: 1, timeLimit: 35 },
  { id: 6, type: 'spatial', question: 'Koji je presek prikazan na slici?', options: ['Krug', 'Trougao', 'Pravougaonik', 'Elipsa'], correctAnswer: 2, timeLimit: 40 },
  { id: 7, type: 'spatial', question: 'Koja je tačka centar rotacije?', options: ['A', 'B', 'C', 'Nijedna'], correctAnswer: 0, timeLimit: 25 },
  { id: 8, type: 'spatial', question: 'Koji objekat je 3D prikaz dvodimenzionalnog lika?', options: ['Kocka', 'Lopta', 'Piramida', 'Valjak'], correctAnswer: 0, timeLimit: 30 },
  { id: 9, type: 'spatial', question: 'Koji je zbir uglova u trouglu?', options: ['90°', '180°', '360°', '270°'], correctAnswer: 1, timeLimit: 20 },
  { id: 10, type: 'spatial', question: 'Koji lik ima 5 temena?', options: ['Trougao', 'Kvadrat', 'Pentaon', 'Heksagon'], correctAnswer: 2, timeLimit: 25 },
  { id: 11, type: 'spatial', question: 'Koji je obim kruga poluprečnika 7 (π≈3.14)?', options: ['21.98', '43.96', '153.86', '307.72'], correctAnswer: 1, timeLimit: 30 },
  { id: 12, type: 'spatial', question: 'Koja je zapremina kocke stranice 5?', options: ['25', '125', '625', '100'], correctAnswer: 1, timeLimit: 25 },
  { id: 13, type: 'spatial', question: 'Koji je zbir unutrašnjih uglova šestougla?', options: ['360°', '540°', '720°', '900°'], correctAnswer: 2, timeLimit: 30 },
  { id: 14, type: 'spatial', question: 'Koja je površina pravougaonika 8x6?', options: ['28', '48', '14', '24'], correctAnswer: 1, timeLimit: 20 },
  { id: 15, type: 'spatial', question: 'Koji ugao je veći od 90°?', options: ['Oštar', 'Pravi', 'Tupi', 'Suplji'], correctAnswer: 2, timeLimit: 20 },
  { id: 16, type: 'spatial', question: 'Koliko stranica ima kocka?', options: ['4', '6', '8', '12'], correctAnswer: 1, timeLimit: 15 },
  { id: 17, type: 'spatial', question: 'Koji je obim kvadrata stranice 9?', options: ['18', '27', '36', '81'], correctAnswer: 2, timeLimit: 15 },
  { id: 18, type: 'spatial', question: 'Koja je dijagonala kvadrata stranice 6?', options: ['6√2', '6', '12', '36'], correctAnswer: 0, timeLimit: 25 },
  { id: 19, type: 'spatial', question: 'Koliko uglova ima osmougao?', options: ['6', '8', '10', '12'], correctAnswer: 1, timeLimit: 15 },
  { id: 20, type: 'spatial', question: 'Koji lik ima sve stranice jednake?', options: ['Pravougaonik', 'Trapez', 'Romb', 'Nijedan'], correctAnswer: 2, timeLimit: 20 },
  { id: 21, type: 'spatial', question: 'Koja je zapremina kocke ivice 3?', options: ['9', '27', '81', '6'], correctAnswer: 1, timeLimit: 20 },
  { id: 22, type: 'spatial', question: 'Koliko temena ima piramida sa četvrtastom osnovom?', options: ['4', '5', '8', '6'], correctAnswer: 1, timeLimit: 20 },
  { id: 23, type: 'spatial', question: 'Koji je zbir spoljašnjih uglova trougla?', options: ['180°', '360°', '540°', '90°'], correctAnswer: 1, timeLimit: 25 },
  { id: 24, type: 'spatial', question: 'Koji oblik ima 12 ivica?', options: ['Kocka', 'Tetraedar', 'Oktaedar', 'Dodekaedar'], correctAnswer: 0, timeLimit: 30 },
  { id: 25, type: 'spatial', question: 'Površina kruga poluprečnika 4 je:', options: ['8π', '16π', '4π', '32π'], correctAnswer: 1, timeLimit: 25 },
  { id: 26, type: 'spatial', question: 'Koji je centar kruga opisanog oko trougla?', options: ['Presek simetrala', 'Presek visina', 'Težište', 'Sve navedeno'], correctAnswer: 3, timeLimit: 35 },
  { id: 27, type: 'spatial', question: 'Koliko dijagonala ima šestougao?', options: ['6', '9', '12', '18'], correctAnswer: 1, timeLimit: 25 },
  { id: 28, type: 'spatial', question: 'Koji geometrijski lik nema simetriju?', options: ['Krug', 'Jednakostranični trougao', 'Paralelogram', 'Romb'], correctAnswer: 2, timeLimit: 25 },
  { id: 29, type: 'spatial', question: 'Površina kocke ivice 2 je:', options: ['8', '12', '24', '4'], correctAnswer: 2, timeLimit: 20 },
  { id: 30, type: 'spatial', question: 'Koji ugao je komplementaran uglu od 40°?', options: ['50°', '140°', '320°', '40°'], correctAnswer: 0, timeLimit: 20 },
  { id: 31, type: 'spatial', question: 'Koji je obim pravougaonika 7x5?', options: ['12', '24', '35', '70'], correctAnswer: 1, timeLimit: 15 },
  { id: 32, type: 'spatial', question: 'Koliko vrhova ima prizma sa trostranom osnovom?', options: ['6', '8', '9', '12'], correctAnswer: 0, timeLimit: 20 },
  { id: 33, type: 'spatial', question: 'Koji lik ima sve uglove prave?', options: ['Kvadrat', 'Romb', 'Trapez', 'Paralelogram'], correctAnswer: 0, timeLimit: 20 },
  { id: 34, type: 'spatial', question: 'Zapremina valjka: r=2, h=5 (π≈3)', options: ['20', '60', '30', '10'], correctAnswer: 1, timeLimit: 25 },
  { id: 35, type: 'spatial', question: 'Koja je stranica trougla ako je P=12 i visina=4?', options: ['3', '6', '8', '16'], correctAnswer: 1, timeLimit: 25 },
  { id: 36, type: 'spatial', question: 'Koliko dijagonala ima četvorougao?', options: ['1', '2', '4', '8'], correctAnswer: 1, timeLimit: 15 },
  { id: 37, type: 'spatial', question: 'Koji oblik ima 20 strana?', options: ['Dodekaedar', 'Ikosaedar', 'Dekagon', 'Oktagon'], correctAnswer: 2, timeLimit: 25 },
  { id: 38, type: 'spatial', question: 'Površina pravougaonika 8x3 je:', options: ['11', '22', '24', '80'], correctAnswer: 2, timeLimit: 15 },
  { id: 39, type: 'spatial', question: 'Koji je poluprečnik kruga opisanog oko kvadrata stranice 6?', options: ['3', '3√2', '6', '6√2'], correctAnswer: 1, timeLimit: 30 },
  { id: 40, type: 'spatial', question: 'Koliko parova paralelnih stranica ima trapez?', options: ['0', '1', '2', '3'], correctAnswer: 1, timeLimit: 20 },
  { id: 41, type: 'spatial', question: 'Koji geometrijski transformacija menja samo položaj?', options: ['Rotacija', 'Homotetija', 'Sličnost', 'Simetrija'], correctAnswer: 0, timeLimit: 25 },
  { id: 42, type: 'spatial', question: 'Zapremina kupe: r=3, h=4 (π≈3)', options: ['12', '36', '108', '24'], correctAnswer: 1, timeLimit: 30 },
  { id: 43, type: 'spatial', question: 'Koji je zbir unutrašnjih uglova petougla?', options: ['360°', '540°', '720°', '900°'], correctAnswer: 1, timeLimit: 25 },
  { id: 44, type: 'spatial', question: 'Koliko prostora zauzimaju 3 kocke ivice 2?', options: ['6', '8', '24', '12'], correctAnswer: 2, timeLimit: 20 },
  { id: 45, type: 'spatial', question: 'Koji lik ima 3 para paralelnih stranica?', options: ['Paralelogram', 'Trapez', 'Prism', 'Heksagon'], correctAnswer: 2, timeLimit: 30 },
  { id: 46, type: 'spatial', question: 'Površina trougla: a=6, h=4:', options: ['24', '12', '10', '48'], correctAnswer: 1, timeLimit: 15 },
  { id: 47, type: 'spatial', question: 'Koji je obim pravilnog šestougla stranice 2?', options: ['6', '8', '12', '24'], correctAnswer: 2, timeLimit: 20 },
  { id: 48, type: 'spatial', question: 'Koliko visina ima piramida sa osnovom kvadrata?', options: ['4', '5', '6', '8'], correctAnswer: 1, timeLimit: 20 },
  { id: 49, type: 'spatial', question: 'Koji je zbir unutrašnjih uglova četvorougla?', options: ['180°', '360°', '540°', '720°'], correctAnswer: 1, timeLimit: 20 },
  { id: 50, type: 'spatial', question: 'Površina kocke ivice 5:', options: ['25', '125', '150', '100'], correctAnswer: 2, timeLimit: 20 },
  { id: 51, type: 'spatial', question: 'Koji oblik ima centar simetrije?', options: ['Jednakokraki trougao', 'Trapez', 'Romb', 'Nijedan'], correctAnswer: 2, timeLimit: 25 },
  { id: 52, type: 'spatial', question: 'Zapremina pravougaonog paralelepipeda 3x4x5:', options: ['12', '20', '60', '94'], correctAnswer: 2, timeLimit: 20 },
  { id: 53, type: 'spatial', question: 'Koliko stranica ima tetraedar?', options: ['4', '6', '8', '12'], correctAnswer: 0, timeLimit: 15 },
  { id: 54, type: 'spatial', question: 'Koji je prečnik kruga opisanog oko trougla?', options: ['a', '2R', 'R/2', 'a√3'], correctAnswer: 1, timeLimit: 30 },
  { id: 55, type: 'spatial', question: 'Površina kruga poluprečnika 5 (π≈3):', options: ['15', '25', '75', '50'], correctAnswer: 2, timeLimit: 20 },
  { id: 56, type: 'spatial', question: 'Koji lik ima sve uglove jednake?', options: ['Romb', 'Trapez', 'Paralelogram', 'Trougao'], correctAnswer: 0, timeLimit: 20 },
  { id: 57, type: 'spatial', question: 'Koliko iznosi ugao jednakostraničnog trougla?', options: ['45°', '60°', '90°', '120°'], correctAnswer: 1, timeLimit: 15 },
  { id: 58, type: 'spatial', question: 'Koji je obim kruga prečnika 10 (π≈3)?', options: ['10', '30', '20', '100'], correctAnswer: 1, timeLimit: 20 },
  { id: 59, type: 'spatial', question: 'Koliko dijagonala iz jednog temena ima osmougao?', options: ['5', '6', '7', '8'], correctAnswer: 1, timeLimit: 25 },
  { id: 60, type: 'spatial', question: 'Koji je zapis Pitagorine teoreme?', options: ['a+b=c', 'a²+b²=c²', 'a²+b²=c', 'a+b²=c²'], correctAnswer: 1, timeLimit: 20 },
  { id: 61, type: 'spatial', question: 'Koliko iznosi treća strana pravouglog trougla ako su katete 3 i 4?', options: ['5', '6', '7', '25'], correctAnswer: 0, timeLimit: 20 },
  { id: 62, type: 'spatial', question: 'Koji oblik ima 8 uglova?', options: ['Heksagon', 'Oktagon', 'Dekagon', 'Tetragon'], correctAnswer: 1, timeLimit: 15 },
  { id: 63, type: 'spatial', question: 'Površina kvadrata dijagonale 8:', options: ['16', '32', '64', '8'], correctAnswer: 1, timeLimit: 25 },
  { id: 64, type: 'spatial', question: 'Koliko parova jednakih stranica ima trapez?', options: ['0', '1', '2', '3'], correctAnswer: 1, timeLimit: 20 },
  { id: 65, type: 'spatial', question: 'Koji geometrijski lik nema dijagonala?', options: ['Trougao', 'Četvorougao', 'Petougao', 'Šestougao'], correctAnswer: 0, timeLimit: 15 },
  { id: 66, type: 'spatial', question: 'Koliko temena ima dodekaedar?', options: ['12', '20', '30', '60'], correctAnswer: 1, timeLimit: 25 },
  { id: 67, type: 'spatial', question: 'Koja je razlika između obima i površine kvadrata?', options: ['Ista', 'Različita', 'Zavisi od stranice', 'Nije uporedivo'], correctAnswer: 3, timeLimit: 20 },
  { id: 68, type: 'spatial', question: 'Koliko strana ima ikosaedar?', options: ['12', '18', '20', '24'], correctAnswer: 2, timeLimit: 25 },
  { id: 69, type: 'spatial', question: 'Koji je zbir uglova u pravilnom šestouglu?', options: ['360°', '540°', '720°', '1080°'], correctAnswer: 2, timeLimit: 25 },
  { id: 70, type: 'spatial', question: 'Površina paralelograma: b=8, v=5:', options: ['13', '40', '26', '80'], correctAnswer: 1, timeLimit: 15 },
  { id: 71, type: 'spatial', question: 'Koji je obim pravilnog trougla stranice 9?', options: ['27', '18', '12', '81'], correctAnswer: 0, timeLimit: 15 },
  { id: 72, type: 'spatial', question: 'Koliko ivica ima prizma sa šeststranom osnovom?', options: ['12', '15', '18', '24'], correctAnswer: 2, timeLimit: 25 },
  { id: 73, type: 'spatial', question: 'Koji geometrijski pojam je definisan kao skup tačaka jednako udaljenih od centra?', options: ['Krug', 'Kružnica', 'Sfera', 'Lopta'], correctAnswer: 1, timeLimit: 25 },
  { id: 74, type: 'spatial', question: 'Koliko iznosi zbir spoljašnjih uglova konveksnog petougla?', options: ['180°', '360°', '540°', '720°'], correctAnswer: 1, timeLimit: 25 },
  { id: 75, type: 'spatial', question: 'Koji je najmanji broj stranica trougla?', options: ['1', '2', '3', '4'], correctAnswer: 2, timeLimit: 10 },
  { id: 76, type: 'spatial', question: 'Koliko uglova ima nonagon?', options: ['7', '9', '11', '18'], correctAnswer: 1, timeLimit: 15 },
  { id: 77, type: 'spatial', question: 'Koji oblik ima 20 dijagonala?', options: ['Oktagon', 'Dekagon', 'Dodekagon', 'Ikosa'], correctAnswer: 1, timeLimit: 30 },
  { id: 78, type: 'spatial', question: 'Površina kruga: d=8 (π≈3):', options: ['12', '48', '24', '16'], correctAnswer: 1, timeLimit: 20 },
  { id: 79, type: 'spatial', question: 'Koliko je роtalnih simetrija ima kvadrat?', options: ['2', '3', '4', '5'], correctAnswer: 2, timeLimit: 25 },
  { id: 80, type: 'spatial', question: 'Koji geometrijski lik je most između 2D i 3D?', options: ['Tačka', 'Linija', 'Ravan', 'Prostor'], correctAnswer: 2, timeLimit: 20 },
  { id: 81, type: 'spatial', question: 'Zapremina sfere r=1 (π≈3):', options: ['3', '4', '12', '1'], correctAnswer: 1, timeLimit: 25 },
  { id: 82, type: 'spatial', question: 'Koliko temena ima oktaedar?', options: ['4', '6', '8', '12'], correctAnswer: 1, timeLimit: 20 },
  { id: 83, type: 'spatial', question: 'Koji je najmanji prostorijski oblik?', options: ['Tačka', 'Linija', 'Ravan', 'Prostor'], correctAnswer: 0, timeLimit: 15 },
  { id: 84, type: 'spatial', question: 'Površina romba: d1=6, d2=8:', options: ['24', '48', '12', '28'], correctAnswer: 0, timeLimit: 25 },
  { id: 85, type: 'spatial', question: 'Koji je obim pravilnog osmougla stranice 3?', options: ['12', '18', '24', '36'], correctAnswer: 2, timeLimit: 20 },

  // LOGICAL - 85 questions
  { id: 86, type: 'logical', question: 'Ako je SVA PTA ptica, a NIKADA ne leti, onda je:', options: ['Svaka ptica leti', 'Neka ptica ne leti', 'Pta ne leti', 'Ništa od navedenog'], correctAnswer: 1, timeLimit: 45 },
  { id: 87, type: 'logical', question: 'Svi A su B. Svi B su C. Zaključak:', options: ['Svi A su C', 'Nijedan A nije C', 'Neki A su C', 'Ništa od navedenog'], correctAnswer: 0, timeLimit: 40 },
  { id: 88, type: 'logical', question: 'Ako je danas ponedeljak, koji je dan za 100 dana?', options: ['Ponedeljak', 'Utorak', 'Sreda', 'Četvrtak'], correctAnswer: 1, timeLimit: 35 },
  { id: 89, type: 'logical', question: 'Koji broj je sledeći: 2, 6, 12, 20, 30, ?', options: ['36', '40', '42', '44'], correctAnswer: 2, timeLimit: 30 },
  { id: 90, type: 'logical', question: 'Ako SVI psi laju i MAX je pas, onda:', options: ['Max ne laje', 'Max laje', 'Možda laje', 'Ništa'], correctAnswer: 1, timeLimit: 30 },
  { id: 91, type: 'logical', question: 'Koja je sledeća boja: crvena, plava, žuta, crvena, plava, ?', options: ['Žuta', 'Zelena', 'Narandžasta', 'Ljubičasta'], correctAnswer: 0, timeLimit: 25 },
  { id: 92, type: 'logical', question: 'Ako je 5 mačaka pojede 5 riba za 5 minuta, koliko treba 100 mačaka za 100 riba?', options: ['5 min', '100 min', '1 min', '50 min'], correctAnswer: 0, timeLimit: 35 },
  { id: 93, type: 'logical', question: 'Koji je logički sled: Ako pada kiša → ulica je mokra. Ulice su suve. Zaključak:', options: ['Pada kiša', 'Ne pada kiša', 'Možda pada', 'Ništa'], correctAnswer: 1, timeLimit: 40 },
  { id: 94, type: 'logical', question: 'Svi X su Y. Neki Y su Z. Zaključak:', options: ['Svi X su Z', 'Neki X su Z', 'Nijedan X nije Z', 'Ne može se zaključiti'], correctAnswer: 3, timeLimit: 45 },
  { id: 95, type: 'logical', question: 'Koji broj nedostaje: 1, 1, 2, 3, 5, 8, 13, ?', options: ['18', '20', '21', '24'], correctAnswer: 2, timeLimit: 25 },
  { id: 96, type: 'logical', question: 'Ako je PETAR otac MARI, a MARI majka JOVANU, ko je Jovan deda od?', options: ['Petar', 'Mari', 'Oboje', 'Niko'], correctAnswer: 0, timeLimit: 35 },
  { id: 97, type: 'logical', question: 'Koja je sledeća cifra: 1, 4, 9, 16, 25, ?', options: ['30', '34', '36', '40'], correctAnswer: 2, timeLimit: 25 },
  { id: 98, type: 'logical', question: 'Ako SVI studenti uče i MARKO student, da li MARKO uči?', options: ['Da', 'Ne', 'Možda', 'Nije sigurno'], correctAnswer: 0, timeLimit: 25 },
  { id: 99, type: 'logical', question: 'Koji je sledeći broj: 3, 5, 9, 15, 23, ?', options: ['31', '33', '35', '37'], correctAnswer: 1, timeLimit: 30 },
  { id: 100, type: 'logical', question: 'Ako je tačno: "Nijedan ptica ne leti", a "Svi orlovi su ptice", zaključak:', options: ['Orlovi lete', 'Orlovi ne lete', 'Neki orlovi lete', 'Ne može se zaključiti'], correctAnswer: 1, timeLimit: 40 },
  { id: 101, type: 'logical', question: 'Ako je 2+2=5, onda je 2+2:', options: ['5', '4', '6', 'Ništa'], correctAnswer: 1, timeLimit: 30 },
  { id: 102, type: 'logical', question: 'Koji broj je sledeći: 1, 4, 8, 16, 32, ?', options: ['48', '64', '40', '56'], correctAnswer: 1, timeLimit: 25 },
  { id: 103, type: 'logical', question: 'Svi ljudi su smrtni. Sokrat je čovek. Zaključak:', options: ['Sokrat je smrtan', 'Sokrat je besmrtan', 'Sokrat je bog', 'Ništa'], correctAnswer: 0, timeLimit: 25 },
  { id: 104, type: 'logical', question: 'Koji dan je bio juče ako je sutra sreda?', options: ['Ponedeljak', 'Utorak', 'Četvrtak', 'Petak'], correctAnswer: 1, timeLimit: 20 },
  { id: 105, type: 'logical', question: 'Ako svi A jesu B, a neki B jesu C, zaključak:', options: ['Svi A jesu C', 'Neki A jesu C', 'Nijedan A nije C', 'Ne može se zaključiti'], correctAnswer: 3, timeLimit: 40 },
  { id: 106, type: 'logical', question: 'Koji je sledeći broj: 2, 3, 5, 9, 17, ?', options: ['25', '33', '31', '29'], correctAnswer: 1, timeLimit: 30 },
  { id: 107, type: 'logical', question: 'Ako je TAMARA sestra MILAN, a MILAN sin OCA, ko je TAMARIN otac?', options: ['Milan', 'Milanov otac', 'Mamin otac', 'Ne može se zaključiti'], correctAnswer: 1, timeLimit: 35 },
  { id: 108, type: 'logical', question: 'Koja reč je nepoznata: KRUG: OKRUG :: KVADRAT : ?', options: ['Pravougaonik', 'Stranica', 'Cetvorostrana', 'Cetvorka'], correctAnswer: 0, timeLimit: 30 },
  { id: 109, type: 'logical', question: 'Ako svi P jesu Q i svi Q jesu R, a ništa nije S, zaključak o P i S:', options: ['P nije S', 'P je S', 'Možda P je S', 'Ništa'], correctAnswer: 0, timeLimit: 45 },
  { id: 110, type: 'logical', question: 'Koji je sledeći: A, C, E, G, I, ?', options: ['J', 'K', 'L', 'M'], correctAnswer: 0, timeLimit: 20 },
  { id: 111, type: 'logical', question: 'Ako je Ivan bolji od Marka, a Marko bolji od Nikole, ko je najgori?', options: ['Ivan', 'Marko', 'Nikola', 'Svi jednaki'], correctAnswer: 2, timeLimit: 20 },
  { id: 112, type: 'logical', question: 'Koji je logički niz: Pondeljak, Sreda, Petak, ?', options: ['Subota', 'Nedelja', 'Utorak', 'Četvrtak'], correctAnswer: 0, timeLimit: 15 },
  { id: 113, type: 'logical', question: 'Ako je SUTRA petak, koji je dan bio prekjuče?', options: ['Sreda', 'Četvrtak', 'Petak', 'Utorak'], correctAnswer: 1, timeLimit: 25 },
  { id: 114, type: 'logical', question: 'Koji broj je neparan i prost između 10 i 20?', options: ['11', '13', '15', '17'], correctAnswer: 0, timeLimit: 20 },
  { id: 115, type: 'logical', question: 'Ako je svaki kvadrat pravougaonik, a svaki pravougaonik paralelogram, zaključak:', options: ['Kvadrat je paralelogram', 'Paralelogram je kvadrat', 'Nisu povezani', 'Ništa'], correctAnswer: 0, timeLimit: 30 },
  { id: 116, type: 'logical', question: 'Koji dan nedelje je uvek između ponedeljka i srede?', options: ['Nedelja', 'Utorak', 'Četvrtak', 'Petak'], correctAnswer: 1, timeLimit: 15 },
  { id: 117, type: 'logical', question: 'Ako 3 osobe sagrade kuću za 6 dana, koliko dana treba 6 osoba?', options: ['3', '6', '2', '12'], correctAnswer: 0, timeLimit: 35 },
  { id: 118, type: 'logical', question: 'Koji je sledeći: J, L, N, P, R, ?', options: ['S', 'T', 'U', 'V'], correctAnswer: 0, timeLimit: 20 },
  { id: 119, type: 'logical', question: 'Ako je svako voće slatko, a banana je voće, zaključak:', options: ['Banana je slatka', 'Banana nije slatka', 'Možda slatka', 'Ništa'], correctAnswer: 0, timeLimit: 25 },
  { id: 120, type: 'logical', question: 'Koji broj je deljiv sa 3 i 4 do 50?', options: ['12', '24', '36', 'Svi navedeni'], correctAnswer: 3, timeLimit: 20 },
  { id: 121, type: 'logical', question: 'Ako je PERO stariji od MARE, a MARA stariji od JOVE, ko je najmlađi?', options: ['Pero', 'Mara', 'Jova', 'Svi isti'], correctAnswer: 2, timeLimit: 20 },
  { id: 122, type: 'logical', question: 'Koji logički sled je ispravan: Ako kiša pada, ulica je mokra. Ulica je mokra. Zaključak:', options: ['Kiša pada', 'Ne pada kiša', 'Možda kiša pada', 'Ništa'], correctAnswer: 2, timeLimit: 35 },
  { id: 123, type: 'logical', question: 'Koji je zbir prvih 10 prirodnih brojeva?', options: ['45', '50', '55', '60'], correctAnswer: 2, timeLimit: 25 },
  { id: 124, type: 'logical', question: 'Ako ništa nije savršeno, a čovek je nešto, zaključak:', options: ['Čovek je savršen', 'Čovek nije savršen', 'Možda', 'Ništa'], correctAnswer: 1, timeLimit: 35 },
  { id: 125, type: 'logical', question: 'Koji je sledeći: 1, 1, 2, 6, 24, ?', options: ['48', '72', '120', '36'], correctAnswer: 2, timeLimit: 30 },
  { id: 126, type: 'logical', question: 'Ako svi pjesnici pišu, a Jovan piše, zaključak:', options: ['Jovan je pjesnik', 'Jovan nije pjesnik', 'Možda', 'Ništa'], correctAnswer: 2, timeLimit: 30 },
  { id: 127, type: 'logical', question: 'Koji je najmanji zajednički sadržalac brojeva 4 i 6?', options: ['12', '24', '6', '2'], correctAnswer: 0, timeLimit: 20 },
  { id: 128, type: 'logical', question: 'Ako je zima hladno, a danas je zima, zaključak:', options: ['Danas je hladno', 'Danas nije hladno', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 25 },
  { id: 129, type: 'logical', question: 'Koji je sledeći: AA, BB, CC, DD, ?', options: ['EE', 'FF', 'GG', 'AA'], correctAnswer: 0, timeLimit: 15 },
  { id: 130, type: 'logical', question: 'Ako svi Srbi piju kafu, a Marko pije čaj, zaključak:', options: ['Marko nije Srbin', 'Marko je Srbin', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 30 },
  { id: 131, type: 'logical', question: 'Koji broj je sledeći: 100, 81, 64, 49, ?', options: ['36', '25', '16', '9'], correctAnswer: 0, timeLimit: 25 },
  { id: 132, type: 'logical', question: 'Ako ništa ne lebdi, a ptica leti, zaključak:', options: ['Ptica ne lebdi', 'Ptica lebdi', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 30 },
  { id: 133, type: 'logical', question: 'Koji je najveći zajednički delilac brojeva 18 i 24?', options: ['6', '12', '3', '2'], correctAnswer: 0, timeLimit: 20 },
  { id: 134, type: 'logical', question: 'Ako je svaki pravougaonik cetvorougao, a kvadrat je pravougaonik, zaključak:', options: ['Kvadrat je cetvorougao', 'Kvadrat nije cetvorougao', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 25 },
  { id: 135, type: 'logical', question: 'Koji je sledeći: 1, 2, 4, 8, 16, 32, ?', options: ['48', '64', '40', '56'], correctAnswer: 1, timeLimit: 20 },
  { id: 136, type: 'logical', question: 'Ako svi avioni lete, a helikopter leti, zaključak:', options: ['Helikopter je avion', 'Helikopter može biti avion', 'Možda', 'Ne može se zaključiti'], correctAnswer: 3, timeLimit: 35 },
  { id: 137, type: 'logical', question: 'Koji je prosek brojeva 10, 20, 30, 40?', options: ['20', '25', '30', '50'], correctAnswer: 1, timeLimit: 20 },
  { id: 138, type: 'logical', question: 'Ako je nebo plavo, a trava zelena, a cvet crven, koja je boja lista?', options: ['Plava', 'Zelena', 'Crvena', 'Žuta'], correctAnswer: 1, timeLimit: 20 },
  { id: 139, type: 'logical', question: 'Koji je sledeći: 2, 6, 12, 20, 30, ?', options: ['40', '42', '44', '46'], correctAnswer: 1, timeLimit: 25 },
  { id: 140, type: 'logical', question: 'Ako nijedan reptil ne leti, a svaki zmaj je reptil, zaključak:', options: ['Zmaj leti', 'Zmaj ne leti', 'Možda', 'Ništa'], correctAnswer: 1, timeLimit: 35 },
  { id: 141, type: 'logical', question: 'Koji je zbir parnih brojeva do 10?', options: ['20', '25', '30', '35'], correctAnswer: 2, timeLimit: 25 },
  { id: 142, type: 'logical', question: 'Ako svi đaci uče, a Marko ne uči, zaključak:', options: ['Marko nije đak', 'Marko je đak', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 30 },
  { id: 143, type: 'logical', question: 'Koji je sledeći: 5, 10, 20, 35, 55, ?', options: ['70', '80', '75', '90'], correctAnswer: 2, timeLimit: 30 },
  { id: 144, type: 'logical', question: 'Ako je uvek dan posle noći, a sada je noć, zaključak:', options: ['Dolazi dan', 'Ne dolazi dan', 'Sada je dan', 'Ništa'], correctAnswer: 0, timeLimit: 25 },
  { id: 145, type: 'logical', question: 'Koji broj je deljiv sa 2, 3 i 5 do 100?', options: ['30', '60', '90', 'Svi navedeni'], correctAnswer: 3, timeLimit: 20 },
  { id: 146, type: 'logical', question: 'Ako svi muškarci imaju браду, a Dejan ima браду, zaključak:', options: ['Dejan je muškarac', 'Dejan nije muškarac', 'Možda', 'Ništa'], correctAnswer: 2, timeLimit: 35 },
  { id: 147, type: 'logical', question: 'Koji je sledeći: 1, 4, 9, 16, 25, 36, ?', options: ['42', '48', '49', '56'], correctAnswer: 2, timeLimit: 20 },
  { id: 148, type: 'logical', question: 'Ako svaki troUGAO ima tri stranice, a figura ima četiri stranice, zaključak:', options: ['Figura je troUGAO', 'Figura nije troUGAO', 'Možda', 'Ništa'], correctAnswer: 1, timeLimit: 30 },
  { id: 149, type: 'logical', question: 'Koji je najmanji prost broj?', options: ['0', '1', '2', '3'], correctAnswer: 2, timeLimit: 10 },
  { id: 150, type: 'logical', question: 'Ako je svaki medved bele boje, a panda je crno-bela, zaključak:', options: ['Panda je medved', 'Panda nije medved', 'Možda', 'Ništa'], correctAnswer: 2, timeLimit: 35 },
  { id: 151, type: 'logical', question: 'Koji je zbir prvih 5 neparnih brojeva?', options: ['15', '20', '25', '30'], correctAnswer: 2, timeLimit: 20 },
  { id: 152, type: 'logical', question: 'Ako svi sportisti trče, a teniser sportista, zaključak:', options: ['Teniser trči', 'Teniser ne trči', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 25 },
  { id: 153, type: 'logical', question: 'Koji je sledeći: 3, 6, 11, 18, 27, ?', options: ['36', '38', '40', '42'], correctAnswer: 1, timeLimit: 30 },
  { id: 154, type: 'logical', question: 'Ako je svaka jabuka voće, a voće raste na drvetu, zaključak:', options: ['Jabuka raste na drvetu', 'Jabuka ne raste na drvetu', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 30 },
  { id: 155, type: 'logical', question: 'Koji je najveći delilac broja 100?', options: ['25', '50', '100', '200'], correctAnswer: 2, timeLimit: 20 },
  { id: 156, type: 'logical', question: 'Ako ništa nije besmrtno, a bogovi su besmrtni, zaključak:', options: ['Bogovi nisu bogovi', 'Bogovi nisu besmrtni', 'Bogovi su besmrtni', 'Bogovi su ljudi'], correctAnswer: 2, timeLimit: 40 },
  { id: 157, type: 'logical', question: 'Koji je sledeći: A, C, F, J, O, ?', options: ['S', 'T', 'U', 'V'], correctAnswer: 0, timeLimit: 35 },
  { id: 158, type: 'logical', question: 'Ako je svaki auto vozilo, a kamion je vozilo, zaključak:', options: ['Kamion je auto', 'Kamion može biti auto', 'Možda', 'Ne može se zaključiti'], correctAnswer: 3, timeLimit: 35 },
  { id: 159, type: 'logical', question: 'Koji je prosek: 5, 10, 15, 20, 25?', options: ['12', '14', '15', '16'], correctAnswer: 2, timeLimit: 20 },
  { id: 160, type: 'logical', question: 'Ako je svaki pas životinja, a mačka nije pas, zaključak:', options: ['Mačka je životinja', 'Mačka nije životinja', 'Možda', 'Ništa'], correctAnswer: 2, timeLimit: 30 },
  { id: 161, type: 'logical', question: 'Koji je sledeći: 7, 14, 21, 28, 35, ?', options: ['40', '42', '44', '46'], correctAnswer: 1, timeLimit: 15 },
  { id: 162, type: 'logical', question: 'Ako je svako drvo biljka, a cvet je biljka, zaključak:', options: ['Cvet je drvo', 'Cvet može biti drvo', 'Možda', 'Ništa'], correctAnswer: 2, timeLimit: 30 },
  { id: 163, type: 'logical', question: 'Koji je zbir svih uglova u paralelogramu?', options: ['180°', '360°', '540°', '720°'], correctAnswer: 1, timeLimit: 25 },
  { id: 164, type: 'logical', question: 'Ako nijedan krug nije kvadrat, a kocka nije krug, zaključak:', options: ['Kocka je kvadrat', 'Kocka nije kvadrat', 'Možda', 'Ništa'], correctAnswer: 2, timeLimit: 40 },
  { id: 165, type: 'logical', question: 'Koji je sledeći: 1, 3, 6, 10, 15, ?', options: ['18', '20', '21', '25'], correctAnswer: 2, timeLimit: 25 },
  { id: 166, type: 'logical', question: 'Ako svi ribari love ribe, a Jovan lovi, zaključak:', options: ['Jovan je ribar', 'Jovan nije ribar', 'Možda', 'Ništa'], correctAnswer: 2, timeLimit: 30 },
  { id: 167, type: 'logical', question: 'Koji je najmanji zajednički sadržalac 8 i 12?', options: ['24', '48', '96', '12'], correctAnswer: 0, timeLimit: 25 },
  { id: 168, type: 'logical', question: 'Ako svaka ptica ima perje, a golub je ptica, zaključak:', options: ['Golub ima perje', 'Golub nema perje', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 25 },
  { id: 169, type: 'logical', question: 'Koji je sledeći: 2, 5, 10, 17, 26, ?', options: ['35', '37', '36', '34'], correctAnswer: 1, timeLimit: 30 },
  { id: 170, type: 'logical', question: 'Ako je svaka knjiga pisan tekst, a roman je knjiga, zaključak:', options: ['Roman je pisan tekst', 'Roman nije pisan tekst', 'Možda', 'Ništa'], correctAnswer: 0, timeLimit: 30 },

  // NUMERICAL - 85 questions
  { id: 211, type: 'numerical', question: 'Koliko je 127 × 4?', options: ['508', '518', '528', '488'], correctAnswer: 0, timeLimit: 30 },
  { id: 212, type: 'numerical', question: 'Koji je prosek brojeva 12, 15, 18, 21, 24?', options: ['17', '18', '19', '20'], correctAnswer: 1, timeLimit: 25 },
  { id: 213, type: 'numerical', question: 'Koliko iznosi 15% od 240?', options: ['30', '36', '42', '48'], correctAnswer: 1, timeLimit: 30 },
  { id: 214, type: 'numerical', question: 'Koji je ostatak pri deljenju 67 sa 7?', options: ['3', '4', '5', '6'], correctAnswer: 4, timeLimit: 25 },
  { id: 215, type: 'numerical', question: 'Ako je x + 5 = 12, koliko je x × 3?', options: ['21', '17', '51', '7'], correctAnswer: 0, timeLimit: 25 },
  { id: 216, type: 'numerical', question: 'Koliko je 2³ × 2²?', options: ['8', '16', '32', '64'], correctAnswer: 2, timeLimit: 30 },
  { id: 217, type: 'numerical', question: 'Koji je najveći zajednički delilac brojeva 24 i 36?', options: ['6', '8', '12', '18'], correctAnswer: 2, timeLimit: 30 },
  { id: 218, type: 'numerical', question: 'Koliko iznosi kvadratni koren iz 144?', options: ['10', '11', '12', '14'], correctAnswer: 2, timeLimit: 20 },
  { id: 219, type: 'numerical', question: 'Ako je 3x + 7 = 22, koliko je x?', options: ['3', '5', '7', '15'], correctAnswer: 1, timeLimit: 25 },
  { id: 220, type: 'numerical', question: 'Koji je procenat: 15 od 75?', options: ['10%', '15%', '20%', '25%'], correctAnswer: 2, timeLimit: 25 },
  { id: 221, type: 'numerical', question: 'Koliko je 25% od 80?', options: ['15', '20', '25', '30'], correctAnswer: 1, timeLimit: 20 },
  { id: 222, type: 'numerical', question: 'Koji je sledeći prost broj posle 7?', options: ['9', '10', '11', '13'], correctAnswer: 2, timeLimit: 20 },
  { id: 223, type: 'numerical', question: 'Ako je 1/4 + 1/4 + 1/2 = x, koliko je x?', options: ['1', '1/2', '1/4', '3/4'], correctAnswer: 0, timeLimit: 25 },
  { id: 224, type: 'numerical', question: 'Koliko je 0.75 kao razlomak u procentima?', options: ['75%', '7.5%', '0.75%', '750%'], correctAnswer: 0, timeLimit: 20 },
  { id: 225, type: 'numerical', question: 'Koji je zapis broja 49 u baznom sistemu?', options: ['7²', '6²+13', '50-1', '7×7'], correctAnswer: 0, timeLimit: 25 },
  { id: 226, type: 'numerical', question: 'Koliko je 456 + 789?', options: ['1235', '1245', '1255', '1145'], correctAnswer: 1, timeLimit: 30 },
  { id: 227, type: 'numerical', question: 'Koji je prosek 100, 200, 300?', options: ['150', '200', '250', '300'], correctAnswer: 1, timeLimit: 20 },
  { id: 228, type: 'numerical', question: 'Koliko iznosi 20% od 350?', options: ['60', '70', '80', '90'], correctAnswer: 1, timeLimit: 25 },
  { id: 229, type: 'numerical', question: 'Koji je ostatak pri deljenju 89 sa 9?', options: ['8', '7', '6', '5'], correctAnswer: 0, timeLimit: 25 },
  { id: 230, type: 'numerical', question: 'Ako je 4x - 5 = 15, koliko je x?', options: ['4', '5', '6', '7'], correctAnswer: 1, timeLimit: 25 },
  { id: 231, type: 'numerical', question: 'Koliko je 5 na treću?', options: ['15', '25', '125', '625'], correctAnswer: 2, timeLimit: 20 },
  { id: 232, type: 'numerical', question: 'Koji je NZD brojeva 15 i 25?', options: ['5', '10', '15', '75'], correctAnswer: 0, timeLimit: 25 },
  { id: 233, type: 'numerical', question: 'Koliki je koren iz 81?', options: ['7', '8', '9', '10'], correctAnswer: 2, timeLimit: 15 },
  { id: 234, type: 'numerical', question: 'Ako je 2x + 8 = 20, koliko je x?', options: ['4', '5', '6', '7'], correctAnswer: 2, timeLimit: 20 },
  { id: 235, type: 'numerical', question: 'Koji procenat: 25 od 200?', options: ['10%', '12.5%', '15%', '20%'], correctAnswer: 1, timeLimit: 25 },
  { id: 236, type: 'numerical', question: 'Koliko je 50% od 88?', options: ['44', '40', '48', '36'], correctAnswer: 0, timeLimit: 15 },
  { id: 237, type: 'numerical', question: 'Koji je sledeći prost broj posle 11?', options: ['12', '13', '14', '15'], correctAnswer: 1, timeLimit: 15 },
  { id: 238, type: 'numerical', question: 'Ako je 1/3 + 1/6 = x, koliko je x?', options: ['1/2', '1/3', '1/6', '2/3'], correctAnswer: 0, timeLimit: 25 },
  { id: 239, type: 'numerical', question: 'Koliko je 0.5 u procentima?', options: ['5%', '50%', '0.5%', '500%'], correctAnswer: 1, timeLimit: 15 },
  { id: 240, type: 'numerical', question: 'Koji je kvadrat broja 12?', options: ['124', '144', '164', '184'], correctAnswer: 1, timeLimit: 20 },
  { id: 241, type: 'numerical', question: 'Koliko je 999 + 111?', options: ['1100', '1110', '1111', '1000'], correctAnswer: 1, timeLimit: 25 },
  { id: 242, type: 'numerical', question: 'Prosek brojeva 5, 10, 15 je:', options: ['8', '10', '12', '15'], correctAnswer: 1, timeLimit: 20 },
  { id: 243, type: 'numerical', question: 'Koliko iznosi 30% od 120?', options: ['30', '34', '36', '40'], correctAnswer: 2, timeLimit: 25 },
  { id: 244, type: 'numerical', question: 'Ostatak pri deljenju 55 sa 6?', options: ['1', '3', '5', '7'], correctAnswer: 0, timeLimit: 20 },
  { id: 245, type: 'numerical', question: 'Ako je x/4 = 9, koliko je x?', options: ['27', '36', '45', '32'], correctAnswer: 1, timeLimit: 20 },
  { id: 246, type: 'numerical', question: 'Koliko je 3 na četvrtu?', options: ['27', '54', '81', '243'], correctAnswer: 2, timeLimit: 25 },
  { id: 247, type: 'numerical', question: 'NZD brojeva 8 i 12:', options: ['2', '4', '6', '8'], correctAnswer: 1, timeLimit: 20 },
  { id: 248, type: 'numerical', question: 'Korjen iz 64:', options: ['6', '7', '8', '9'], correctAnswer: 2, timeLimit: 15 },
  { id: 249, type: 'numerical', question: 'Ako je 5x = 35, x = ?', options: ['5', '6', '7', '8'], correctAnswer: 2, timeLimit: 20 },
  { id: 250, type: 'numerical', question: 'Procenat: 8 od 32?', options: ['20%', '25%', '30%', '35%'], correctAnswer: 1, timeLimit: 25 },
  { id: 251, type: 'numerical', question: 'Koliko je 75% od 60?', options: ['40', '45', '48', '50'], correctAnswer: 1, timeLimit: 20 },
  { id: 252, type: 'numerical', question: 'Sledeći prost posle 17?', options: ['18', '19', '20', '21'], correctAnswer: 1, timeLimit: 15 },
  { id: 253, type: 'numerical', question: '2/5 + 1/5 = ?', options: ['3/10', '3/5', '1/5', '2/5'], correctAnswer: 1, timeLimit: 25 },
  { id: 254, type: 'numerical', question: '0.25 kao procenat:', options: ['2.5%', '25%', '0.25%', '250%'], correctAnswer: 1, timeLimit: 20 },
  { id: 255, type: 'numerical', question: '11 na kvadrat:', options: ['111', '121', '131', '141'], correctAnswer: 1, timeLimit: 15 },
  { id: 256, type: 'numerical', question: 'Koliko je 234 × 2?', options: ['468', '478', '488', '458'], correctAnswer: 0, timeLimit: 30 },
  { id: 257, type: 'numerical', question: 'Prosek 15, 25, 35:', options: ['20', '25', '30', '35'], correctAnswer: 1, timeLimit: 20 },
  { id: 258, type: 'numerical', question: '10% od 550:', options: ['50', '55', '60', '65'], correctAnswer: 1, timeLimit: 25 },
  { id: 259, type: 'numerical', question: 'Ostatak 73/8:', options: ['7', '8', '9', '6'], correctAnswer: 0, timeLimit: 25 },
  { id: 260, type: 'numerical', question: 'Ako je 6y = 42, y = ?', options: ['5', '6', '7', '8'], correctAnswer: 2, timeLimit: 20 },
  { id: 261, type: 'numerical', question: '4 na petu:', options: ['64', '256', '512', '1024'], correctAnswer: 3, timeLimit: 30 },
  { id: 262, type: 'numerical', question: 'NZD(18,27):', options: ['3', '6', '9', '18'], correctAnswer: 2, timeLimit: 25 },
  { id: 263, type: 'numerical', question: 'Korjen iz 169:', options: ['11', '12', '13', '14'], correctAnswer: 2, timeLimit: 20 },
  { id: 264, type: 'numerical', question: '7z = 63, z = ?', options: ['7', '8', '9', '10'], correctAnswer: 2, timeLimit: 20 },
  { id: 265, type: 'numerical', question: '9 u procentima od 45?', options: ['15%', '18%', '20%', '25%'], correctAnswer: 2, timeLimit: 25 },
  { id: 266, type: 'numerical', question: '60% od 85:', options: ['45', '48', '51', '54'], correctAnswer: 2, timeLimit: 25 },
  { id: 267, type: 'numerical', question: 'Prost posle 23?', options: ['24', '25', '26', '27'], correctAnswer: 2, timeLimit: 15 },
  { id: 268, type: 'numerical', question: '1 - 3/4 = ?', options: ['1/4', '1/2', '3/4', '1'], correctAnswer: 0, timeLimit: 20 },
  { id: 269, type: 'numerical', question: '0.125 u procentima:', options: ['1.25%', '12.5%', '125%', '0.125%'], correctAnswer: 1, timeLimit: 25 },
  { id: 270, type: 'numerical', question: '13 na kvadrat:', options: ['156', '166', '169', '176'], correctAnswer: 2, timeLimit: 20 },
  { id: 271, type: 'numerical', question: '888 + 222:', options: ['1010', '1100', '1110', '1000'], correctAnswer: 2, timeLimit: 25 },
  { id: 272, type: 'numerical', question: 'Prosek 8, 12, 20:', options: ['12', '13', '14', '15'], correctAnswer: 2, timeLimit: 20 },
  { id: 273, type: 'numerical', question: '5% od 800:', options: ['35', '40', '45', '50'], correctAnswer: 1, timeLimit: 20 },
  { id: 274, type: 'numerical', question: 'Ostatak 91/13:', options: ['0', '1', '2', '7'], correctAnswer: 0, timeLimit: 25 },
  { id: 275, type: 'numerical', question: '8k = 96, k = ?', options: ['10', '11', '12', '13'], correctAnswer: 2, timeLimit: 20 },
  { id: 276, type: 'numerical', question: '2 na desetu:', options: ['512', '1024', '2048', '4096'], correctAnswer: 1, timeLimit: 30 },
  { id: 277, type: 'numerical', question: 'NZD(30,45):', options: ['5', '10', '15', '30'], correctAnswer: 2, timeLimit: 25 },
  { id: 278, type: 'numerical', question: 'Korjen iz 225:', options: ['13', '14', '15', '16'], correctAnswer: 2, timeLimit: 20 },
  { id: 279, type: 'numerical', question: '9m = 81, m = ?', options: ['7', '8', '9', '10'], correctAnswer: 2, timeLimit: 20 },
  { id: 280, type: 'numerical', question: 'Procenat: 18 od 90?', options: ['15%', '18%', '20%', '25%'], correctAnswer: 2, timeLimit: 25 },
  { id: 281, type: 'numerical', question: '40% od 75:', options: ['25', '28', '30', '35'], correctAnswer: 2, timeLimit: 25 },
  { id: 282, type: 'numerical', question: 'Prost posle 29?', options: ['30', '31', '32', '33'], correctAnswer: 1, timeLimit: 15 },
  { id: 283, type: 'numerical', question: '3/5 - 1/5 = ?', options: ['2/5', '4/5', '2/10', '1/5'], correctAnswer: 0, timeLimit: 25 },
  { id: 284, type: 'numerical', question: '0.2 u procentima:', options: ['2%', '20%', '0.2%', '200%'], correctAnswer: 1, timeLimit: 20 },
  { id: 285, type: 'numerical', question: '15 na kvadrat:', options: ['215', '225', '235', '245'], correctAnswer: 1, timeLimit: 20 },

  // VERBAL - 85 questions
  { id: 286, type: 'verbal', question: 'SINONIM: "Inteligentan" je najsličniji sa:', options: ['Glup', 'Bistar', ' spor', 'Miran'], correctAnswer: 1, timeLimit: 20 },
  { id: 287, type: 'verbal', question: 'ANTONIM: "Konfuzija" je suprotno od:', options: ['Jasnost', 'Red', 'Mir', 'Sreća'], correctAnswer: 0, timeLimit: 20 },
  { id: 288, type: 'verbal', question: 'SINONIM: "Brz" je najsličniji sa:', options: [' spor', 'Hitar', 'Lenj', 'Stal'], correctAnswer: 1, timeLimit: 20 },
  { id: 289, type: 'verbal', question: 'ANTONIM: "Globalno" je suprotno od:', options: ['Svetski', 'Lokalno', 'Univerzalno', 'Opšte'], correctAnswer: 1, timeLimit: 25 },
  { id: 290, type: 'verbal', question: 'Koja reč ne pripada istoj grupi: pas, mačka, konj, auto?', options: ['Pas', 'Mačka', 'Konj', 'Auto'], correctAnswer: 3, timeLimit: 20 },
  { id: 291, type: 'verbal', question: 'Koja reč je sinonim za "ekstraordinaran"?', options: ['Običan', 'Normalan', 'Vanredan', 'Loš'], correctAnswer: 2, timeLimit: 25 },
  { id: 292, type: 'verbal', question: 'Koja reč je antonim za "permanentan"?', options: ['Stalan', 'Privremen', 'Večan', 'Trajan'], correctAnswer: 1, timeLimit: 25 },
  { id: 293, type: 'verbal', question: 'Dovršite: Brzo kao ___', options: ['Puž', 'Gepard', 'Kornjača', 'Skoro'], correctAnswer: 1, timeLimit: 20 },
  { id: 294, type: 'verbal', question: 'Koja reč je treća u abecedi?', options: ['A', 'C', 'B', 'D'], correctAnswer: 2, timeLimit: 15 },
  { id: 295, type: 'verbal', question: 'SINONIM: "Akcija" je najsličniji sa:', options: ['Pasivnost', 'Radnja', 'Misao', 'Mir'], correctAnswer: 1, timeLimit: 20 },
  { id: 296, type: 'verbal', question: 'Koja reč je suprotna značenju "sinteza"?', options: ['Analiza', 'Kombinacija', 'Spoj', 'Rastavljanje'], correctAnswer: 0, timeLimit: 25 },
  { id: 297, type: 'verbal', question: 'Koja reč ne pripada grupi: jabuka, kruška, banana, šporet?', options: ['Jabuka', 'Kruška', 'Banana', 'Šporet'], correctAnswer: 3, timeLimit: 20 },
  { id: 298, type: 'verbal', question: 'ANTONIM: "Apsolutno" je supotno od:', options: ['Potpuno', 'Relativno', 'Svakako', 'Definitivno'], correctAnswer: 1, timeLimit: 25 },
  { id: 299, type: 'verbal', question: 'SINONIM za "fleksibilan":', options: ['Kruto', 'Savitljivo', 'Čvrsto', 'Fiksno'], correctAnswer: 1, timeLimit: 20 },
  { id: 300, type: 'verbal', question: 'Koja reč je uvek tačna: Svi ___ imaju srce.', options: ['Ljudi', 'Psi', 'RibE', 'Mačke'], correctAnswer: 0, timeLimit: 25 },
  { id: 301, type: 'verbal', question: 'ANTONIM: "Mlad" je suprotno od:', options: ['Stariji', 'Star', 'Mladost', 'Nov'], correctAnswer: 1, timeLimit: 20 },
  { id: 302, type: 'verbal', question: 'SINONIM: "Tuga" je najsličnije sa:', options: ['Radost', 'Žalost', 'Mir', 'Ljutnja'], correctAnswer: 1, timeLimit: 20 },
  { id: 303, type: 'verbal', question: 'Koja reč ne pripada: more, reka, jezero, planina?', options: ['More', 'Reka', 'Jezero', 'Planina'], correctAnswer: 3, timeLimit: 20 },
  { id: 304, type: 'verbal', question: 'ANTONIM: "Prijatelj" je suprotno od:', options: ['Drug', 'Neprijatelj', ' poznanik', 'Savetnik'], correctAnswer: 1, timeLimit: 20 },
  { id: 305, type: 'verbal', question: 'SINONIM: "Hitar" je najsličnije sa:', options: [' spor', 'Brz', 'Lenj', 'Oprezan'], correctAnswer: 1, timeLimit: 20 },
  { id: 306, type: 'verbal', question: 'Koja reč ne pripada: auto, avion, brod, kuća?', options: ['Auto', 'Avion', 'Brod', 'Kuća'], correctAnswer: 3, timeLimit: 20 },
  { id: 307, type: 'verbal', question: 'ANTONIM: "Svetlo" je suprotno od:', options: ['Dan', 'Mračno', 'Sunce', 'Sijalica'], correctAnswer: 1, timeLimit: 20 },
  { id: 308, type: 'verbal', question: 'SINONIM: "Jak" je najsličnije sa:', options: ['Slab', 'Snažan', 'Stariji', 'Novi'], correctAnswer: 1, timeLimit: 20 },
  { id: 309, type: 'verbal', question: 'Koja reč ne pripada: kralj, kraljica, car, princ?', options: ['Kralj', 'Kraljica', 'Car', 'Vitez'], correctAnswer: 3, timeLimit: 20 },
  { id: 310, type: 'verbal', question: 'ANTONIM: "Tiho" je suprotno od:', options: ['Mirno', 'Glasno', 'Tih', 'Spokojno'], correctAnswer: 1, timeLimit: 20 },
  { id: 311, type: 'verbal', question: 'SINONIM: "Glup" je najsličnije sa:', options: ['Bistar', 'Budala', 'Pametan', 'Sposoban'], correctAnswer: 1, timeLimit: 20 },
  { id: 312, type: 'verbal', question: 'Koja reč ne pripada: Srbija, Hrvatska, Bosna, Beograd?', options: ['Srbija', 'Hrvatska', 'Bosna', 'Beograd'], correctAnswer: 3, timeLimit: 20 },
  { id: 313, type: 'verbal', question: 'ANTONIM: "Bogat" je suprotno od:', options: ['Para', 'Siromašan', 'Novac', 'Plemenit'], correctAnswer: 1, timeLimit: 20 },
  { id: 314, type: 'verbal', question: 'SINONIM: "Stari" je najsličnije sa:', options: ['Nov', 'Star', 'Mlad', 'Svež'], correctAnswer: 1, timeLimit: 20 },
  { id: 315, type: 'verbal', question: 'Koja reč ne pripada: jabuka, banana, kajsija, krompir?', options: ['Jabuka', 'Banana', 'Kajsija', 'Krompir'], correctAnswer: 3, timeLimit: 20 },
  { id: 316, type: 'verbal', question: 'ANTONIM: "Prazno" je suprotno od:', options: ['Puno', 'Praznina', 'Prazan', 'Null'], correctAnswer: 0, timeLimit: 20 },
  { id: 317, type: 'verbal', question: 'SINONIM: "Miran" je najsličnije sa:', options: ['Nemiran', 'Staložen', 'Uznemiren', 'Nervozan'], correctAnswer: 1, timeLimit: 20 },
  { id: 318, type: 'verbal', question: 'Koja reč ne pripada: ptica, riba, pas, auto?', options: ['Ptica', 'Riba', 'Pas', 'Auto'], correctAnswer: 3, timeLimit: 20 },
  { id: 319, type: 'verbal', question: 'ANTONIM: "Toplo" je suprotno od:', options: ['Vruće', 'Hladno', 'Zimsko', 'Letnje'], correctAnswer: 1, timeLimit: 20 },
  { id: 320, type: 'verbal', question: 'SINONIM: "Loš" je najsličnije sa:', options: ['Dobar', 'Rđav', 'Odličan', 'Super'], correctAnswer: 1, timeLimit: 20 },
  { id: 321, type: 'verbal', question: 'Koja reč ne pripada: Madrid, Beograd, Pariz, London?', options: ['Madrid', 'Beograd', 'Pariz', 'Rim'], correctAnswer: 3, timeLimit: 20 },
  { id: 322, type: 'verbal', question: 'ANTONIM: "Snažan" je suprotno od:', options: ['Jak', 'Slab', 'Moćan', 'Silan'], correctAnswer: 1, timeLimit: 20 },
  { id: 323, type: 'verbal', question: 'SINONIM: "Pravi" je najsličnije sa:', options: ['Lažan', 'Istinit', 'Neistinit', 'Tačan'], correctAnswer: 1, timeLimit: 20 },
  { id: 324, type: 'verbal', question: 'Koja reč ne pripada: lonac, tanjir, viljuška, grad?', options: ['Lonac', 'Tanjir', 'Viljuška', 'Grad'], correctAnswer: 3, timeLimit: 20 },
  { id: 325, type: 'verbal', question: 'ANTONIM: "Skup" je suprotno od:', options: ['Skupo', 'Jeftin', 'Skuplji', 'Najskuplji'], correctAnswer: 1, timeLimit: 20 },
  { id: 326, type: 'verbal', question: 'SINONIM: "Pametan" je najsličnije sa:', options: ['Glu', 'Bistar', 'Spor', 'Nepažljiv'], correctAnswer: 1, timeLimit: 20 },
  { id: 327, type: 'verbal', question: 'Koja reč ne pripada: zima, proleće, jesen, noć?', options: ['Zima', 'Proleće', 'Jesen', 'Noć'], correctAnswer: 3, timeLimit: 20 },
  { id: 328, type: 'verbal', question: 'ANTONIM: "Brz" je suprotno od:', options: ['Hitar', ' spor', 'Fleksibilan', 'Pokretljiv'], correctAnswer: 1, timeLimit: 20 },
  { id: 329, type: 'verbal', question: 'SINONIM: "Miris" je najsličnije sa:', options: ['Smrad', 'Vonj', 'Aroma', 'Zadah'], correctAnswer: 2, timeLimit: 20 },
  { id: 330, type: 'verbal', question: 'Koja reč ne pripada: sto, stolica, krevet, reka?', options: ['Sto', 'Stolica', 'Krevet', 'Reka'], correctAnswer: 3, timeLimit: 20 },
  { id: 331, type: 'verbal', question: 'ANTONIM: "Lepa" je suprotno od:', options: ['Lep', 'Ružan', 'Zgodan', 'Umiljat'], correctAnswer: 1, timeLimit: 20 },
  { id: 332, type: 'verbal', question: 'SINONIM: "Mokar" je najsličnije sa:', options: ['Suh', 'Vlažan', 'Suvo', 'Nepromokao'], correctAnswer: 1, timeLimit: 20 },
  { id: 333, type: 'verbal', question: 'Koja reč ne pripada: pas, mačka, krava, točak?', options: ['Pas', 'Mačka', 'Krava', 'Točak'], correctAnswer: 3, timeLimit: 20 },
  { id: 334, type: 'verbal', question: 'ANTONIM: "Prav" je suprotno od:', options: ['Ravnan', 'Kriv', 'Pravilan', 'Izravnat'], correctAnswer: 1, timeLimit: 20 },
  { id: 335, type: 'verbal', question: 'SINONIM: "Hrabar" je najsličnije sa:', options: ['Kukavica', 'Sramežljiv', 'Odvažan', 'Stidljiv'], correctAnswer: 2, timeLimit: 20 },
  { id: 336, type: 'verbal', question: 'Koja reč ne pripada: more, okean, reka, bazen?', options: ['More', 'Okean', 'Reka', 'Bazen'], correctAnswer: 3, timeLimit: 20 },
  { id: 337, type: 'verbal', question: 'ANTONIM: "Tezak" je suprotno od:', options: ['Težak', 'Lagan', 'Masivan', 'Snažan'], correctAnswer: 1, timeLimit: 20 },
  { id: 338, type: 'verbal', question: 'SINONIM: "Stidljiv" je najsličnije sa:', options: ['Hrabar', 'Sramežljiv', 'Drzak', 'Otvoren'], correctAnswer: 1, timeLimit: 20 },
  { id: 339, type: 'verbal', question: 'Koja reč ne pripada: pčela, mrav, pauk, leptir?', options: ['Pčela', 'Mrav', 'Pauk', 'Leptir'], correctAnswer: 2, timeLimit: 20 },
  { id: 340, type: 'verbal', question: 'ANTONIM: "Otvoren" je suprotno od:', options: ['Otvoren', 'Zatvoren', 'Prost', 'Slobodan'], correctAnswer: 1, timeLimit: 20 },
  { id: 341, type: 'verbal', question: 'SINONIM: "Glad" je najsličnije sa:', options: ['Sit', 'Nezasićen', 'Pun', 'Site'], correctAnswer: 1, timeLimit: 20 },
  { id: 342, type: 'verbal', question: 'Koja reč ne pripada: knjiga, sveska, olovka, oblak?', options: ['Knjiga', 'Sveska', 'Olovka', 'Oblak'], correctAnswer: 3, timeLimit: 20 },
  { id: 343, type: 'verbal', question: 'ANTONIM: "Mlad" je suprotno od:', options: ['Mlad', 'Star', 'Nevina', 'Svež'], correctAnswer: 1, timeLimit: 20 },
  { id: 344, type: 'verbal', question: 'SINONIM: "Gladan" je najsličnije sa:', options: ['Sit', 'Nezasićen', 'Pun', 'Sit'], correctAnswer: 1, timeLimit: 20 },
  { id: 345, type: 'verbal', question: 'Koja reč ne pripada: avion, auto, brod, sat?', options: ['Avion', 'Auto', 'Brod', 'Sat'], correctAnswer: 3, timeLimit: 20 },
  { id: 346, type: 'verbal', question: 'ANTONIM: "Jasan" je suprotno od:', options: ['Jasan', 'Konfuzan', 'Svetao', 'Bistar'], correctAnswer: 1, timeLimit: 20 },
  { id: 347, type: 'verbal', question: 'SINONIM: "Plač" je najsličnije sa:', options: ['Smijeh', 'Suze', 'Radost', 'Veselje'], correctAnswer: 1, timeLimit: 20 },
  { id: 348, type: 'verbal', question: 'Koja reč ne pripada: sunce, mesec, zvezda, automobil?', options: ['Sunce', 'Mesec', 'Zvezda', 'Automobil'], correctAnswer: 3, timeLimit: 20 },
  { id: 349, type: 'verbal', question: 'ANTONIM: "Pravilan" je suprotno od:', options: ['Nepravilan', 'Kriv', 'Prav', 'Ispravan'], correctAnswer: 1, timeLimit: 20 },
  { id: 350, type: 'verbal', question: 'SINONIM: "Crven" je najsličnije sa:', options: ['Plav', 'Al', 'Zelen', 'Žut'], correctAnswer: 1, timeLimit: 20 },
  { id: 351, type: 'verbal', question: 'Koja reč ne pripada: nebo, zemlja, more, mesec?', options: ['Nebo', 'Zemlja', 'More', 'Mesec'], correctAnswer: 3, timeLimit: 20 },
  { id: 352, type: 'verbal', question: 'ANTONIM: "Ćutljiv" je suprotno od:', options: ['Tih', 'Prijedljiv', 'Nem', 'Mir'], correctAnswer: 1, timeLimit: 20 },
  { id: 353, type: 'verbal', question: 'SINONIM: "Površan" je najsličnije sa:', options: ['Dubok', 'Plitak', 'Tanak', 'Lagan'], correctAnswer: 1, timeLimit: 20 },
  { id: 354, type: 'verbal', question: 'Koja reč ne pripada: sto, lampa, prozor, drvo?', options: ['Sto', 'Lampa', 'Prozor', 'Drvo'], correctAnswer: 3, timeLimit: 20 },
  { id: 355, type: 'verbal', question: 'ANTONIM: "Snažan" je suprotno od:', options: ['Jakim', 'Slabim', 'Moćnim', 'Snažnim'], correctAnswer: 1, timeLimit: 20 },
  { id: 356, type: 'verbal', question: 'SINONIM: "Potrebno" je najsličnije sa:', options: ['Neobično', 'Neophodno', 'Suvišno', 'Lako'], correctAnswer: 1, timeLimit: 20 },
  { id: 357, type: 'verbal', question: 'Koja reč ne pripada: voda, vatra, zemlja, kuća?', options: ['Voda', 'Vatra', 'Zemlja', 'Kuća'], correctAnswer: 3, timeLimit: 20 },
  { id: 358, type: 'verbal', question: 'ANTONIM: "Rđav" je suprotno od:', options: ['Loš', 'Dobar', 'Za', 'Nedob'], correctAnswer: 1, timeLimit: 20 },
  { id: 359, type: 'verbal', question: 'SINONIM: "Jednostavan" je najsličnije sa:', options: ['Komplikovan', 'Lak', 'Težak', 'Nezgodan'], correctAnswer: 1, timeLimit: 20 },
  { id: 360, type: 'verbal', question: 'Koja reč ne pripada: mleko, voda, sok, pivo?', options: ['Mleko', 'Voda', 'Sok', 'Pivo'], correctAnswer: 3, timeLimit: 20 },
  { id: 361, type: 'verbal', question: 'ANTONIM: "Brzina" je suprotno od:', options: ['Sporost', 'Brz', 'Tempo', 'Hod'], correctAnswer: 0, timeLimit: 20 },
  { id: 362, type: 'verbal', question: 'SINONIM: "Nezgodan" je najsličnije sa:', options: ['Zgodan', 'Neprijatan', 'Prijatelj', 'Lagan'], correctAnswer: 1, timeLimit: 20 },
  { id: 363, type: 'verbal', question: 'Koja reč ne pripada: sneg, kiša, vetar, sto?', options: ['Sneg', 'Kiša', 'Vetar', 'Sto'], correctAnswer: 3, timeLimit: 20 },
  { id: 364, type: 'verbal', question: 'ANTONIM: "Mladost" je suprotno od:', options: ['Mladi', 'Starost', 'Detinjstvo', 'Zrelost'], correctAnswer: 1, timeLimit: 20 },
  { id: 365, type: 'verbal', question: 'SINONIM: "Prijateljski" je najsličnije sa:', options: ['Neprijateljski', 'Prijatelj', 'Nezainteresovan', 'Hladan'], correctAnswer: 1, timeLimit: 20 },
  { id: 366, type: 'verbal', question: 'Koja reč ne pripada: mama, tata, sestra, komšija?', options: ['Mama', 'Tata', 'Sestra', 'Komšija'], correctAnswer: 3, timeLimit: 20 },
  { id: 367, type: 'verbal', question: 'ANTONIM: "Plodan" je suprotno od:', options: ['Rodan', 'Nevodan', 'Plod', 'Bogat'], correctAnswer: 1, timeLimit: 20 },
  { id: 368, type: 'verbal', question: 'SINONIM: "Nevolja" je najsličnije sa:', options: ['Sreća', 'Problem', 'Radost', 'Užitak'], correctAnswer: 1, timeLimit: 20 },
  { id: 369, type: 'verbal', question: 'Koja reč ne pripada: pesma, film, knjiga, zid?', options: ['Pesma', 'Film', 'Knjiga', 'Zid'], correctAnswer: 3, timeLimit: 20 },
  { id: 370, type: 'verbal', question: 'ANTONIM: "Bogatstvo" je suprotno od:', options: ['Novac', 'Siromaštvo', 'Blago', 'Imanje'], correctAnswer: 1, timeLimit: 20 },

  // GENERAL KNOWLEDGE - 85 questions
  { id: 371, type: 'general', question: 'Koji je glavni grad Francuske?', options: ['London', 'Berlin', 'Pariz', 'Madrid'], correctAnswer: 2, timeLimit: 15 },
  { id: 372, type: 'general', question: 'Koja planeta je najbliža Suncu?', options: ['Venera', 'Merkur', 'Mars', 'Jupiter'], correctAnswer: 1, timeLimit: 15 },
  { id: 373, type: 'general', question: 'Ko je napisao "Gorski vijenac"?', options: ['Ivo Andrić', 'Petar II Petrović Njegoš', 'Milan Kundera', 'Danilo Kiš'], correctAnswer: 1, timeLimit: 20 },
  { id: 374, type: 'general', question: 'Koliko kontinenata postoji?', options: ['5', '6', '7', '8'], correctAnswer: 2, timeLimit: 15 },
  { id: 375, type: 'general', question: 'Koji je najduži put na svetu?', options: ['Put svile', 'Pan-American highway', 'Trans-Sibirska železnica', 'Autoput 66'], correctAnswer: 1, timeLimit: 25 },
  { id: 376, type: 'general', question: 'Koji hemijski element ima simbol "Au"?', options: ['Srebro', 'Zlato', 'Aluminijum', 'Argon'], correctAnswer: 1, timeLimit: 15 },
  { id: 377, type: 'general', question: 'Godine 1945. završen je Drugi svetski rat. Koja zemlja je bila saveznik?', options: ['Nemačka', 'Italija', 'SAD i Velika Britanija', 'Japan'], correctAnswer: 2, timeLimit: 20 },
  { id: 378, type: 'general', question: 'Koji je najveći okean?', options: ['Atlantski', 'Indijski', 'Tihi', 'Arktički'], correctAnswer: 2, timeLimit: 15 },
  { id: 379, type: 'general', question: 'Ko je izumio telefon?', options: ['Thomas Edison', 'Nikola Tesla', 'Alexander Graham Bell', 'Benjamin Franklin'], correctAnswer: 2, timeLimit: 20 },
  { id: 380, type: 'general', question: 'Koja država ima najviše stanovnika?', options: ['Indija', 'Kina', 'SAD', 'Rusija'], correctAnswer: 1, timeLimit: 15 },
  { id: 381, type: 'general', question: 'Koji je najviši vrh na svetu?', options: ['K2', 'Mont Blanc', 'Everest', 'Kilimandžaro'], correctAnswer: 2, timeLimit: 15 },
  { id: 382, type: 'general', question: 'U kom veku je pada Rimska imperija?', options: ['III vek', 'V vek', 'VII vek', 'X vek'], correctAnswer: 1, timeLimit: 20 },
  { id: 383, type: 'general', question: 'Koji je zvanični jezik u Brazilu?', options: ['Španski', 'Portugalski', 'Engleski', 'Francuski'], correctAnswer: 1, timeLimit: 15 },
  { id: 384, type: 'general', question: 'Koliko minuta ima jedan dan?', options: ['860', '1440', '2400', '1200'], correctAnswer: 1, timeLimit: 15 },
  { id: 385, type: 'general', question: 'Koji je bio prvi čovek na Mesecu?', options: ['Buzz Aldrin', 'Neil Armstrong', 'Yuri Gagarin', 'Michael Collins'], correctAnswer: 1, timeLimit: 20 },
  { id: 386, type: 'general', question: 'Koji je glavni grad Italije?', options: ['Rim', 'Milan', 'Venecija', 'Firenca'], correctAnswer: 0, timeLimit: 15 },
  { id: 387, type: 'general', question: 'Koja je najmanja planeta u Sunčevom sistemu?', options: ['Merkur', 'Mars', 'Venera', 'Pluto'], correctAnswer: 0, timeLimit: 20 },
  { id: 388, type: 'general', question: 'Ko je napisao "Na Drini ćuprija"?', options: ['Ivo Andrić', 'Milan Kundera', 'Danilo Kiš', 'Miloš Crnjanski'], correctAnswer: 0, timeLimit: 20 },
  { id: 389, type: 'general', question: 'Koliko država čini EU?', options: ['25', '27', '30', '28'], correctAnswer: 1, timeLimit: 20 },
  { id: 390, type: 'general', question: 'Koji je najduži most na svetu?', options: ['Most u Đingšanu', 'Golden Gate', 'Mackinac', 'Brooklyn'], correctAnswer: 0, timeLimit: 25 },
  { id: 391, type: 'general', question: 'Koji hemijski element ima simbol "Fe"?', options: ['Zlato', 'Srebro', 'Gvožđe', 'Bakar'], correctAnswer: 2, timeLimit: 15 },
  { id: 392, type: 'general', question: 'Koji je bio prvi svetski rat?', options: ['1914-1918', '1939-1945', '1918-1939', '1945-1990'], correctAnswer: 0, timeLimit: 20 },
  { id: 393, type: 'general', question: 'Koji je najmanji kontinent?', options: ['Evropa', 'Antarktik', 'Australija', 'Južna Amerika'], correctAnswer: 2, timeLimit: 15 },
  { id: 394, type: 'general', question: 'Ko je izumio struju?', options: ['Nikola Tesla', 'Thomas Edison', 'Benjamin Franklin', 'Albert Einstein'], correctAnswer: 1, timeLimit: 20 },
  { id: 395, type: 'general', question: 'Koliko država ima SAD?', options: ['48', '50', '52', '49'], correctAnswer: 1, timeLimit: 15 },
  { id: 396, type: 'general', question: 'Koji je najduži put u Evropi?', options: ['Trans-evropski', 'Euroroad', 'Trans-Sibir', 'Put svile'], correctAnswer: 1, timeLimit: 25 },
  { id: 397, type: 'general', question: 'Koji hemijski element je "Ag"?', options: ['Zlato', 'Srebro', 'Aluminijum', 'Argon'], correctAnswer: 1, timeLimit: 15 },
  { id: 398, type: 'general', question: 'Kada je počeo Drugi svetski rat?', options: ['1935', '1939', '1941', '1945'], correctAnswer: 1, timeLimit: 20 },
  { id: 399, type: 'general', question: 'Koji je najhladniji kontinent?', options: ['Arktik', 'Antarktik', 'Severna Amerika', 'Evropa'], correctAnswer: 1, timeLimit: 15 },
  { id: 400, type: 'general', question: 'Ko je izumio antibiotike?', options: ['Alexander Fleming', 'Louis Pasteur', 'Marie Curie', 'Isaac Newton'], correctAnswer: 0, timeLimit: 20 },
  { id: 401, type: 'general', question: 'Koji je najveći grad u svetu po broju stanovnika?', options: ['Njujork', 'Tokio', 'Šangaj', 'Mumbaj'], correctAnswer: 1, timeLimit: 20 },
  { id: 402, type: 'general', question: 'Koliko vremena treba svetlosti da stigne do Meseca?', options: ['1 sekunda', '1 minut', '1 sat', '1 dan'], correctAnswer: 1, timeLimit: 25 },
  { id: 403, type: 'general', question: 'Koji je glavni grad Japana?', options: ['Osaka', 'Kobe', 'Tokio', 'Kiot'], correctAnswer: 2, timeLimit: 15 },
  { id: 404, type: 'general', question: 'Koliko planeta ima Sunčev sistem?', options: ['7', '8', '9', '10'], correctAnswer: 1, timeLimit: 15 },
  { id: 405, type: 'general', question: 'Ko je napisao "Kraljević Marko"?', options: ['Ivan Goran Kovačić', 'Ivan Mažuranić', 'Petar Preradović', 'Dimitrije Mitrinović'], correctAnswer: 1, timeLimit: 25 },
  { id: 406, type: 'general', question: 'Koliko vremena treba Zemlji da obiđe Sunce?', options: ['365 dana', '366 dana', '360 dana', '365.25 dana'], correctAnswer: 0, timeLimit: 20 },
  { id: 407, type: 'general', question: 'Koja je najveća пустиња на свету?', options: ['Sahara', 'Gobi', 'Antarktik', 'Kalahari'], correctAnswer: 2, timeLimit: 20 },
  { id: 408, type: 'general', question: 'Ko je otkrio Ameriku?', options: ['Magelan', 'Kolumbo', 'Vasko da Gama', 'Amerigo Vespuči'], correctAnswer: 1, timeLimit: 20 },
  { id: 409, type: 'general', question: 'Koliko prosečno traje trudnoća kod čoveka?', options: ['6 meseci', '7 meseci', '9 meseci', '10 meseci'], correctAnswer: 2, timeLimit: 15 },
  { id: 410, type: 'general', question: 'Koji je glavni grad Nemačke?', options: ['Minhen', 'Berlin', 'Hamburg', 'Frankfurt'], correctAnswer: 1, timeLimit: 15 },
  { id: 411, type: 'general', question: 'Koliko iznosi brzina svetlosti?', options: ['300.000 km/s', '150.000 km/s', '1.000.000 km/s', '3.000 km/s'], correctAnswer: 0, timeLimit: 25 },
  { id: 412, type: 'general', question: 'Koji je najveći okean?', options: ['Tihi', 'Atlantski', 'Indijski', 'Arktički'], correctAnswer: 0, timeLimit: 15 },
  { id: 413, type: 'general', question: 'Ko je naslikao "Mona Lizu"?', options: ['Michelangelo', 'Leonardo da Vinci', 'Raffaello', 'Donatello'], correctAnswer: 1, timeLimit: 20 },
  { id: 414, type: 'general', question: 'Koliko sekundi ima jedan sat?', options: ['3600', '360', '60', '6000'], correctAnswer: 0, timeLimit: 15 },
  { id: 415, type: 'general', question: 'Koji je najviši vodopad na svetu?', options: ['Anđeoski vodopad', 'Nagaral', 'Iguazu', 'Viktorija'], correctAnswer: 0, timeLimit: 25 },
  { id: 416, type: 'general', question: 'Koji je glavni grad Španije?', options: ['Barselona', 'Valensija', 'Madrid', 'Sevilja'], correctAnswer: 2, timeLimit: 15 },
  { id: 417, type: 'general', question: 'Koliko meseci ima godina?', options: ['10', '11', '12', '13'], correctAnswer: 2, timeLimit: 10 },
  { id: 418, type: 'general', question: 'Ko je bio prvi predsednik SAD?', options: ['Abraham Linkoln', 'Džordž Vašington', 'Tomas Džeferson', 'Džon Adams'], correctAnswer: 1, timeLimit: 20 },
  { id: 419, type: 'general', question: 'Koja je najveća država na svetu?', options: ['Kina', 'Kanada', 'SAD', 'Rusija'], correctAnswer: 3, timeLimit: 15 },
  { id: 420, type: 'general', question: 'Koliko kostiju ima ljudsko telo?', options: ['186', '206', '256', '306'], correctAnswer: 1, timeLimit: 25 },
  { id: 421, type: 'general', question: 'Koji je glavni grad Engleske?', options: ['Birmingem', 'London', 'Mančester', 'Liverpul'], correctAnswer: 1, timeLimit: 15 },
  { id: 422, type: 'general', question: 'Koja je najviša planina u Evropi?', options: ['Mont Blank', 'Everest', 'Kilimandžaro', 'Elbrus'], correctAnswer: 0, timeLimit: 20 },
  { id: 423, type: 'general', question: 'Koliko mišića ima ljudsko telo?', options: ['400', '500', '600', '700'], correctAnswer: 2, timeLimit: 25 },
  { id: 424, type: 'general', question: 'Koji je najduži most u Evropi?', options: ['Most u Lisbonu', 'Oresund', 'Most u Rijeci', 'Golden Gate'], correctAnswer: 1, timeLimit: 25 },
  { id: 425, type: 'general', question: 'Koji je glavni grad Rusije?', options: ['Sankt Peterburg', 'Moskva', 'Kijev', 'Soči'], correctAnswer: 1, timeLimit: 15 },
  { id: 426, type: 'general', question: 'Koji je najveći kontinent?', options: ['Azija', 'Afrika', 'Severna Amerika', 'Evropa'], correctAnswer: 0, timeLimit: 15 },
  { id: 427, type: 'general', question: 'Koliko procenata vode ima ljudsko telo?', options: ['50%', '60%', '70%', '80%'], correctAnswer: 1, timeLimit: 25 },
  { id: 428, type: 'general', question: 'Koji je najduži tunel na svetu?', options: ['La Manche', 'Seikan', 'Gotard', 'Eurot'], correctAnswer: 1, timeLimit: 25 },
  { id: 429, type: 'general', question: 'Koji je glavni grad Kine?', options: ['Hong Kong', 'Peking', 'Šangaj', 'Peking'], correctAnswer: 1, timeLimit: 15 },
  { id: 430, type: 'general', question: 'Koliko zuba ima odrasli čovek?', options: ['28', '30', '32', '34'], correctAnswer: 2, timeLimit: 20 },
  { id: 431, type: 'general', question: 'Koji je najveći остров на свету?', options: ['Madagaskar', 'Grenland', 'Nova Gvineja', 'Borneo'], correctAnswer: 1, timeLimit: 20 },
  { id: 432, type: 'general', question: 'Koji je glavni grad Australije?', options: ['Sidnej', 'Melburn', 'Canberra', 'Brisbejn'], correctAnswer: 2, timeLimit: 20 },
  { id: 433, type: 'general', question: 'Koliko ima glavnih boja?', options: ['3', '5', '7', '10'], correctAnswer: 2, timeLimit: 15 },
  { id: 434, type: 'general', question: 'Koji je najveći most u svetu po dužini?', options: ['Džingšan', 'Golden Gate', 'Millau', 'Akashi'], correctAnswer: 0, timeLimit: 25 },
  { id: 435, type: 'general', question: 'Koji je glavni grad Kanade?', options: ['Toronto', 'Vankuver', 'Otava', 'Montreal'], correctAnswer: 2, timeLimit: 20 },
  { id: 436, type: 'general', question: 'Koliko nogu ima pauk?', options: ['6', '8', '10', '12'], correctAnswer: 1, timeLimit: 15 },
  { id: 437, type: 'general', question: 'Koja je najduža reka u Evropi?', options: ['Dunav', 'Volga', 'Rajna', 'Loara'], correctAnswer: 1, timeLimit: 25 },
  { id: 438, type: 'general', question: 'Koji je glavni grad Indije?', options: ['Mumbaj', 'Kalkata', 'New Delhi', 'Čenaj'], correctAnswer: 2, timeLimit: 20 },
  { id: 439, type: 'general', question: 'Koliko krila ima pčela?', options: ['2', '4', '6', '8'], correctAnswer: 1, timeLimit: 15 },
  { id: 440, type: 'general', question: 'Koja je najviša zgrada na svetu?', options: ['Taipei 101', 'Burj Khalifa', 'Shanghai Tower', 'One World Trade'], correctAnswer: 1, timeLimit: 20 },
  { id: 441, type: 'general', question: 'Koji je glavni grad Turske?', options: ['Istanbul', 'Ankara', 'Izmir', 'Antalija'], correctAnswer: 1, timeLimit: 15 },
  { id: 442, type: 'general', question: 'Koliko nogu ima kraba?', options: ['6', '8', '10', '12'], correctAnswer: 1, timeLimit: 15 },
  { id: 443, type: 'general', question: 'Koji je najduži niz željeznice?', options: ['Trans-Sibirski', 'Trans-Kanadski', 'Trans-Australijski', 'Trans-Amerzijski'], correctAnswer: 0, timeLimit: 25 },
  { id: 444, type: 'general', question: 'Koji je glavni grad Argentine?', options: ['Kordoba', 'Buenos Aires', 'Rosario', 'Mendoza'], correctAnswer: 1, timeLimit: 20 },
  { id: 445, type: 'general', question: 'Koliko nogu ima obična bubamara?', options: ['4', '6', '8', '10'], correctAnswer: 1, timeLimit: 15 },
  { id: 446, type: 'general', question: 'Koji je najveći nacionalni park u svetu?', options: ['Yellowstone', 'Gronland', 'Zvonceg', 'Kongof'], correctAnswer: 1, timeLimit: 30 },
  { id: 447, type: 'general', question: 'Koji je glavni grad Meksika?', options: ['Gvadalahara', 'Meksiko Siti', 'Monterej', 'Kankun'], correctAnswer: 1, timeLimit: 15 },
  { id: 448, type: 'general', question: 'Koliko srce kuca u minuti prosečno?', options: ['40-60', '60-100', '100-140', '140-180'], correctAnswer: 1, timeLimit: 20 },
  { id: 449, type: 'general', question: 'Koji je najpoznatiji muzej na svetu?', options: ['Louvre', 'Metropolitan', 'British Museum', 'Prado'], correctAnswer: 0, timeLimit: 20 },
  { id: 450, type: 'general', question: 'Koji je glavni grad Grčke?', options: ['Solun', 'Atina', 'Patra', 'Iraklion'], correctAnswer: 1, timeLimit: 15 },
  { id: 451, type: 'general', question: 'Koliko godina živi prosekso ljudski život?', options: ['50', '60', '70', '80'], correctAnswer: 2, timeLimit: 15 },
  { id: 452, type: 'general', question: 'Koji je najduži фjорд на свету?', options: ['Sognefjord', 'Milford', 'Geiranger', 'Harder'], correctAnswer: 0, timeLimit: 30 },
  { id: 453, type: 'general', question: 'Koji je glavni grad Poljske?', options: ['Krakov', 'Varšava', 'Gdansk', 'Poznan'], correctAnswer: 1, timeLimit: 15 },
  { id: 454, type: 'general', question: 'Koliko dlana ima ljudska ruka?', options: ['4', '5', '6', '7'], correctAnswer: 1, timeLimit: 15 },
  { id: 455, type: 'general', question: 'Koji je najveći pustinjski grad na svetu?', options: ['Kairo', 'Dubai', 'Las Vegas', 'Zianda'], correctAnswer: 1, timeLimit: 30 },

  // WORLD FLAGS - 100 questions with images
  { id: 76, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇳', options: ['Kina', 'SAD', 'Rusija', 'EU'], correctAnswer: 0, timeLimit: 15 },
  { id: 77, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇺🇸', options: ['SAD', 'Kanada', 'Australija', 'Britanija'], correctAnswer: 0, timeLimit: 15 },
  { id: 78, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇬🇧', options: ['Britanija', 'Australija', 'Novi Zeland', 'Kanada'], correctAnswer: 0, timeLimit: 15 },
  { id: 79, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇫🇷', options: ['Francuska', 'Holandija', 'Italija', 'Irska'], correctAnswer: 0, timeLimit: 15 },
  { id: 80, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇩🇪', options: ['Nemačka', 'Belgija', 'Rumunija', 'Uganda'], correctAnswer: 0, timeLimit: 15 },
  { id: 81, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇮🇹', options: ['Italija', 'Mađarska', 'Meksiko', 'Irak'], correctAnswer: 0, timeLimit: 15 },
  { id: 82, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇪🇸', options: ['Španija', 'Meksiko', 'Kolumbija', 'Argentina'], correctAnswer: 0, timeLimit: 15 },
  { id: 83, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇷🇺', options: ['Rusija', 'Holandija', 'Francuska', 'Srbija'], correctAnswer: 0, timeLimit: 15 },
  { id: 84, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇯🇵', options: ['Japan', 'Južna Koreja', 'Bangladeš', 'Palestina'], correctAnswer: 0, timeLimit: 15 },
  { id: 85, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇰🇷', options: ['Južna Koreja', 'Severna Koreja', 'Kina', 'Vijetnam'], correctAnswer: 0, timeLimit: 15 },
  { id: 86, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇦', options: ['Kanada', 'SAD', 'Britanija', 'Australija'], correctAnswer: 0, timeLimit: 15 },
  { id: 87, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇺', options: ['Australija', 'Novi Zeland', 'Britanija', 'Kanada'], correctAnswer: 0, timeLimit: 15 },
  { id: 88, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇷', options: ['Brazil', 'Argentina', 'Čile', 'Peru'], correctAnswer: 0, timeLimit: 15 },
  { id: 89, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇮🇳', options: ['Indija', 'Pakistan', 'Bangladesh', 'Nepal'], correctAnswer: 0, timeLimit: 15 },
  { id: 90, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇵🇰', options: ['Pakistan', 'Indija', 'Turska', 'Alžir'], correctAnswer: 0, timeLimit: 15 },
  { id: 91, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇹🇷', options: ['Turska', 'Pakistan', 'Alžir', 'Tunis'], correctAnswer: 0, timeLimit: 15 },
  { id: 92, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇦', options: ['Saudijska Arabija', 'UAE', 'Katar', 'Kuvajt'], correctAnswer: 0, timeLimit: 15 },
  { id: 93, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇪', options: ['UAE', 'Saudijska Arabija', 'Katar', 'Kuvajt'], correctAnswer: 0, timeLimit: 15 },
  { id: 94, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇮🇱', options: ['Izrael', 'Palestina', 'Liban', 'Jordan'], correctAnswer: 0, timeLimit: 15 },
  { id: 95, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇭', options: ['Švajcarska', 'Švedska', 'Austrija', 'Finska'], correctAnswer: 0, timeLimit: 15 },
  { id: 96, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇹', options: ['Austrija', 'Švajcarska', 'Mađarska', 'Poljska'], correctAnswer: 0, timeLimit: 15 },
  { id: 97, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇪', options: ['Belgija', 'Nemačka', 'Holandija', 'Luksemburg'], correctAnswer: 0, timeLimit: 15 },
  { id: 98, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇳🇱', options: ['Holandija', 'Belgija', 'Luksemburg', 'Rusija'], correctAnswer: 0, timeLimit: 15 },
  { id: 99, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇵🇱', options: ['Poljska', 'Francuska', 'Italija', 'Monako'], correctAnswer: 0, timeLimit: 15 },
  { id: 100, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇪', options: ['Švedska', 'Norveška', 'Finska', 'Danska'], correctAnswer: 0, timeLimit: 15 },
  { id: 101, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇳🇴', options: ['Norveška', 'Švedska', 'Finska', 'Danska'], correctAnswer: 0, timeLimit: 15 },
  { id: 102, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇩🇰', options: ['Danska', 'Norveška', 'Švedska', 'Finska'], correctAnswer: 0, timeLimit: 15 },
  { id: 103, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇫🇮', options: ['Finska', 'Švedska', 'Norveška', 'Estonija'], correctAnswer: 0, timeLimit: 15 },
  { id: 104, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇬🇷', options: ['Grčka', 'Kipar', 'Albanija', 'Makedonija'], correctAnswer: 0, timeLimit: 15 },
  { id: 105, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇵🇹', options: ['Portugal', 'Španija', 'Italija', 'Brazil'], correctAnswer: 0, timeLimit: 15 },
  { id: 106, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇮🇪', options: ['Irska', 'Britanija', 'Kanada', 'Australija'], correctAnswer: 0, timeLimit: 15 },
  { id: 107, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇷', options: ['Argentina', 'Brazil', 'Urugvaj', 'Paragvaj'], correctAnswer: 0, timeLimit: 15 },
  { id: 108, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇴', options: ['Kolumbija', 'Venecuela', 'Ekvador', 'Peru'], correctAnswer: 0, timeLimit: 15 },
  { id: 109, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇱', options: ['Čile', 'Peru', 'Bolivija', 'Argentina'], correctAnswer: 0, timeLimit: 15 },
  { id: 110, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇵🇪', options: ['Peru', 'Kolumbija', 'Čile', 'Bolivija'], correctAnswer: 0, timeLimit: 15 },
  { id: 111, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇽', options: ['Meksiko', 'Španija', 'Italija', 'Filipini'], correctAnswer: 0, timeLimit: 15 },
  { id: 112, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇻🇪', options: ['Venecuela', 'Kolumbija', 'Ekvador', 'Peru'], correctAnswer: 0, timeLimit: 15 },
  { id: 113, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇪🇬', options: ['Egipat', 'Sudan', 'Etiopija', 'Libija'], correctAnswer: 0, timeLimit: 15 },
  { id: 114, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇿🇦', options: ['Južna Afrika', 'Namibija', 'Bocvana', 'Zimbabve'], correctAnswer: 0, timeLimit: 15 },
  { id: 115, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇳🇬', options: ['Nigerija', 'Kamerun', 'Gana', 'Kenija'], correctAnswer: 0, timeLimit: 15 },
  { id: 116, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇰🇪', options: ['Kenija', 'Tanzanija', 'Uganda', 'Etiopija'], correctAnswer: 0, timeLimit: 15 },
  { id: 117, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇦', options: ['Maroko', 'Alžir', 'Tunis', 'Libija'], correctAnswer: 0, timeLimit: 15 },
  { id: 118, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇩🇿', options: ['Alžir', 'Maroko', 'Tunis', 'Libija'], correctAnswer: 0, timeLimit: 15 },
  { id: 119, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇹🇳', options: ['Tunis', 'Maroko', 'Alžir', 'Libija'], correctAnswer: 0, timeLimit: 15 },
  { id: 120, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇮🇷', options: ['Iran', 'Irak', 'Avganistan', 'Pakistan'], correctAnswer: 0, timeLimit: 15 },
  { id: 121, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇮🇶', options: ['Irak', 'Iran', 'Sirija', 'Jordan'], correctAnswer: 0, timeLimit: 15 },
  { id: 122, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇾', options: ['Sirija', 'Irak', 'Jordan', 'Liban'], correctAnswer: 0, timeLimit: 15 },
  { id: 123, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇯🇴', options: ['Jordan', 'Sirija', 'Irak', 'Palestina'], correctAnswer: 0, timeLimit: 15 },
  { id: 124, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇱🇧', options: ['Liban', 'Sirija', 'Jordan', 'Izrael'], correctAnswer: 0, timeLimit: 15 },
  { id: 125, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇲', options: ['Jermenija', 'Azerbejdžan', 'Gruzija', 'Turska'], correctAnswer: 0, timeLimit: 15 },
  { id: 126, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇿', options: ['Azerbejdžan', 'Jermenija', 'Gruzija', 'Iran'], correctAnswer: 0, timeLimit: 15 },
  { id: 127, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇬🇪', options: ['Gruzija', 'Jermenija', 'Azerbejdžan', 'Rusija'], correctAnswer: 0, timeLimit: 15 },
  { id: 128, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇺🇦', options: ['Ukrajina', 'Rusija', 'Belorusija', 'Moldavija'], correctAnswer: 0, timeLimit: 15 },
  { id: 129, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇾', options: ['Belorusija', 'Ukrajina', 'Rusija', 'Poljska'], correctAnswer: 0, timeLimit: 15 },
  { id: 130, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇩', options: ['Moldavija', 'Rumunija', 'Ukrajina', 'Belorusija'], correctAnswer: 0, timeLimit: 15 },
  { id: 131, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇷🇴', options: ['Rumunija', 'Moldavija', 'Mađarska', 'Bugarska'], correctAnswer: 0, timeLimit: 15 },
  { id: 132, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇬', options: ['Bugarska', 'Rumunija', 'Grčka', 'Srbija'], correctAnswer: 0, timeLimit: 15 },
  { id: 133, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇷🇸', options: ['Srbija', 'Crna Gora', 'Bosna', 'Hrvatska'], correctAnswer: 0, timeLimit: 15 },
  { id: 134, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇪', options: ['Crna Gora', 'Srbija', 'Bosna', 'Hrvatska'], correctAnswer: 0, timeLimit: 15 },
  { id: 135, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇭🇷', options: ['Hrvatska', 'Slovenija', 'Bosna', 'Srbija'], correctAnswer: 0, timeLimit: 15 },
  { id: 136, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇮', options: ['Slovenija', 'Hrvatska', 'Austrija', 'Italija'], correctAnswer: 0, timeLimit: 15 },
  { id: 137, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇰', options: ['Severna Makedonija', 'Grčka', 'Albanija', 'Bugarska'], correctAnswer: 0, timeLimit: 15 },
  { id: 138, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇱', options: ['Albanija', 'Kosovo', 'Crna Gora', 'Makedonija'], correctAnswer: 0, timeLimit: 15 },
  { id: 139, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇿', options: ['Češka', 'Slovačka', 'Poljska', 'Austrija'], correctAnswer: 0, timeLimit: 15 },
  { id: 140, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇰', options: ['Slovačka', 'Češka', 'Mađarska', 'Poljska'], correctAnswer: 0, timeLimit: 15 },
  { id: 141, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇭🇺', options: ['Mađarska', 'Rumunija', 'Slovačka', 'Austrija'], correctAnswer: 0, timeLimit: 15 },
  { id: 142, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇵🇱', options: ['Poljska', 'Češka', 'Slovačka', 'Litvanija'], correctAnswer: 0, timeLimit: 15 },
  { id: 143, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇱🇹', options: ['Litvanija', 'Letonija', 'Estonija', 'Poljska'], correctAnswer: 0, timeLimit: 15 },
  { id: 144, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇱🇻', options: ['Letonija', 'Litvanija', 'Estonija', 'Rusija'], correctAnswer: 0, timeLimit: 15 },
  { id: 145, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇪🇪', options: ['Estonija', 'Letonija', 'Litvanija', 'Finska'], correctAnswer: 0, timeLimit: 15 },
  { id: 146, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇳🇿', options: ['Novi Zeland', 'Australija', 'Britanija', 'Kanada'], correctAnswer: 0, timeLimit: 15 },
  { id: 147, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇵🇭', options: ['Filipini', 'Indonezija', 'Malezija', 'Tajland'], correctAnswer: 0, timeLimit: 15 },
  { id: 148, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇮🇩', options: ['Indonezija', 'Malezija', 'Filipini', 'Singapur'], correctAnswer: 0, timeLimit: 15 },
  { id: 149, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇾', options: ['Malezija', 'Indonezija', 'Brunej', 'Singapur'], correctAnswer: 0, timeLimit: 15 },
  { id: 150, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇬', options: ['Singapur', 'Malezija', 'Brunej', 'Tajland'], correctAnswer: 0, timeLimit: 15 },
  { id: 151, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇹🇭', options: ['Tajland', 'Laos', 'Kambodža', 'Mjanmar'], correctAnswer: 0, timeLimit: 15 },
  { id: 152, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇻🇳', options: ['Vijetnam', 'Kina', 'Laos', 'Kambodža'], correctAnswer: 0, timeLimit: 15 },
  { id: 153, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇰🇭', options: ['Kambodža', 'Tajland', 'Laos', 'Vijetnam'], correctAnswer: 0, timeLimit: 15 },
  { id: 154, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇱🇦', options: ['Laos', 'Tajland', 'Kambodža', 'Vijetnam'], correctAnswer: 0, timeLimit: 15 },
  { id: 155, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇲', options: ['Mjanmar', 'Tajland', 'Bangladeš', 'Indija'], correctAnswer: 0, timeLimit: 15 },
  { id: 156, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇩', options: ['Bangladeš', 'Indija', 'Mjanmar', 'Nepal'], correctAnswer: 0, timeLimit: 15 },
  { id: 157, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇳🇵', options: ['Nepal', 'Tibet', 'Indija', 'Kina'], correctAnswer: 0, timeLimit: 15 },
  { id: 158, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇹', options: ['Butan', 'Nepal', 'Tibet', 'Indija'], correctAnswer: 0, timeLimit: 15 },
  { id: 159, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇱🇰', options: ['Šri Lanka', 'Indija', 'Maldivi', 'Bangladeš'], correctAnswer: 0, timeLimit: 15 },
  { id: 160, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇻', options: ['Maldivi', 'Šri Lanka', 'Indija', 'Indonezija'], correctAnswer: 0, timeLimit: 15 },
  { id: 161, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇳', options: ['Kina', 'Koreja', 'Japan', 'Vijetnam'], correctAnswer: 0, timeLimit: 15 },
  { id: 162, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇴', options: ['Makao', 'Hong Kong', 'Kina', 'Tajvan'], correctAnswer: 0, timeLimit: 15 },
  { id: 163, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇭🇰', options: ['Hong Kong', 'Makao', 'Kina', 'Britanija'], correctAnswer: 0, timeLimit: 15 },
  { id: 164, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇹🇼', options: ['Tajvan', 'Kina', 'Hong Kong', 'Japan'], correctAnswer: 0, timeLimit: 15 },
  { id: 165, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇰🇵', options: ['Severna Koreja', 'Južna Koreja', 'Kina', 'Rusija'], correctAnswer: 0, timeLimit: 15 },
  { id: 166, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇳', options: ['Mongolija', 'Kina', 'Rusija', 'Kazahstan'], correctAnswer: 0, timeLimit: 15 },
  { id: 167, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇰🇿', options: ['Kazahstan', 'Uzbekistan', 'Turkmenistan', 'Kiri'], correctAnswer: 0, timeLimit: 15 },
  { id: 168, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇺🇿', options: ['Uzbekistan', 'Kazahstan', 'Tadžikistan', 'Turkmenistan'], correctAnswer: 0, timeLimit: 15 },
  { id: 169, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇹🇯', options: ['Tadžikistan', 'Uzbekistan', 'Kini', 'Avganistan'], correctAnswer: 0, timeLimit: 15 },
  { id: 170, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇹🇲', options: ['Turkmenistan', 'Uzbekistan', 'Kazahstan', 'Iran'], correctAnswer: 0, timeLimit: 15 },
  { id: 171, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇰🇬', options: ['Kiri', 'Kazahstan', 'Uzbekistan', 'Mongolija'], correctAnswer: 0, timeLimit: 15 },
  { id: 172, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇫', options: ['Avganistan', 'Pakistan', 'Iran', 'Tadžikistan'], correctAnswer: 0, timeLimit: 15 },
  { id: 173, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇱🇧', options: ['Liban', 'Sirija', 'Jordan', 'Izrael'], correctAnswer: 0, timeLimit: 15 },
  { id: 174, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇶🇦', options: ['Katar', 'UAE', 'Kuvajt', 'Saudijska Arabija'], correctAnswer: 0, timeLimit: 15 },
  { id: 175, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇰🇼', options: ['Kuvajt', 'Katar', 'UAE', 'Saudijska Arabija'], correctAnswer: 0, timeLimit: 15 },
  { id: 176, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇭', options: ['Bahrein', 'Katar', 'UAE', 'Kuvajt'], correctAnswer: 0, timeLimit: 15 },
  { id: 177, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇴🇲', options: ['Oman', 'Jemen', 'UAE', 'Saudijska Arabija'], correctAnswer: 0, timeLimit: 15 },
  { id: 178, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇾🇪', options: ['Jemen', 'Oman', 'Saudijska Arabija', 'Etiopija'], correctAnswer: 0, timeLimit: 15 },
  { id: 179, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇪🇹', options: ['Etiopija', 'Eritreja', 'Somalija', 'Džibuti'], correctAnswer: 0, timeLimit: 15 },
  { id: 180, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇴', options: ['Somalija', 'Etiopija', 'Džibuti', 'Kenija'], correctAnswer: 0, timeLimit: 15 },
  { id: 181, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇩🇯', options: ['Džibuti', 'Eritreja', 'Somalija', 'Etiopija'], correctAnswer: 0, timeLimit: 15 },
  { id: 182, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇪🇷', options: ['Eritreja', 'Džibuti', 'Etiopija', 'Sudan'], correctAnswer: 0, timeLimit: 15 },
  { id: 183, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇩', options: ['Sudan', 'Egipt', 'Etiopija', 'Eritreja'], correctAnswer: 0, timeLimit: 15 },
  { id: 184, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇸🇸', options: ['Južni Sudan', 'Sudan', 'Kenija', 'Etiopija'], correctAnswer: 0, timeLimit: 15 },
  { id: 185, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇲', options: ['Kamerun', 'Nigerija', 'Gabon', 'Kongo'], correctAnswer: 0, timeLimit: 15 },
  { id: 186, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇬🇶', options: ['Ekvatorijalna Gvineja', 'Gabon', 'Kamerun', 'Kongo'], correctAnswer: 0, timeLimit: 15 },
  { id: 187, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇬🇦', options: ['Gabon', 'Kamerun', 'Ekvatorijalna Gvineja', 'Kongo'], correctAnswer: 0, timeLimit: 15 },
  { id: 188, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇬', options: ['Kongo', 'Gabon', 'Kamerun', 'Centralnoafrička Rep.'], correctAnswer: 0, timeLimit: 15 },
  { id: 189, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇨🇩', options: ['DR Kongo', 'Kongo', 'Ruanda', 'Burundi'], correctAnswer: 0, timeLimit: 15 },
  { id: 190, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇷🇼', options: ['Ruanda', 'Burundi', 'Uganda', 'Tanzanija'], correctAnswer: 0, timeLimit: 15 },
  { id: 191, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇮', options: ['Burundi', 'Ruanda', 'Tanzanija', 'Kongo'], correctAnswer: 0, timeLimit: 15 },
  { id: 192, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇺🇬', options: ['Uganda', 'Kenija', 'Tanzanija', 'Ruanda'], correctAnswer: 0, timeLimit: 15 },
  { id: 193, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇹🇿', options: ['Tanzanija', 'Kenija', 'Uganda', 'Mozambik'], correctAnswer: 0, timeLimit: 15 },
  { id: 194, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇿🇲', options: ['Zambija', 'Zimbabve', 'Malavi', 'Mozambik'], correctAnswer: 0, timeLimit: 15 },
  { id: 195, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇿🇼', options: ['Zimbabve', 'Zambija', 'Bocvana', 'Mozambik'], correctAnswer: 0, timeLimit: 15 },
  { id: 196, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇧🇼', options: ['Bocvana', 'Zimbabve', 'Zambija', 'Namibija'], correctAnswer: 0, timeLimit: 15 },
  { id: 197, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇳🇦', options: ['Namibija', 'Bocvana', 'JAR', 'Angola'], correctAnswer: 0, timeLimit: 15 },
  { id: 198, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇿', options: ['Mozambik', 'Tanzanija', 'Zambija', 'Malavi'], correctAnswer: 0, timeLimit: 15 },
  { id: 199, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇦🇩', options: ['Andora', 'Španija', 'Francuska', 'Italija'], correctAnswer: 0, timeLimit: 15 },
  { id: 200, type: 'flags', question: 'Kojoj državi pripada ova zastava?', image: '🇲🇨', options: ['Monako', 'Francuska', 'Italija', 'Španija'], correctAnswer: 0, timeLimit: 15 },
]

const TYPE_LABELS: Record<QuestionType, string> = {
  spatial: 'Prostorno',
  logical: 'Logičko',
  numerical: 'Numeričko',
  verbal: 'Verbalno',
  general: 'Opšta Kultura',
  flags: 'Zastave'
}

const TYPE_COLORS: Record<QuestionType, string> = {
  spatial: 'from-purple-500 to-indigo-500',
  logical: 'from-blue-500 to-cyan-500',
  numerical: 'from-green-500 to-emerald-500',
  verbal: 'from-orange-500 to-amber-500',
  general: 'from-pink-500 to-rose-500',
  flags: 'from-teal-500 to-cyan-500'
}

const DEFAULT_CONFIG: CategoryConfig = {
  spatial: 3,
  logical: 3,
  numerical: 3,
  verbal: 3,
  general: 3,
  flags: 3
}

const MAX_TOTAL_QUESTIONS = 20

export default function IntelligenceTestPage() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [timeLeft, setTimeLeft] = useState(30)
  const [testStarted, setTestStarted] = useState(false)
  const [testCompleted, setTestCompleted] = useState(false)
  const [startTime, setStartTime] = useState<number>(0)
  const [categoryConfig, setCategoryConfig] = useState<CategoryConfig>(DEFAULT_CONFIG)
  const [selectedQuestions, setSelectedQuestions] = useState<Question[]>([])

  const totalSelected = Object.values(categoryConfig).reduce((a, b) => a + b, 0)

  const generateQuestions = () => {
    const questions: Question[] = []
    const usedIds = new Set<number>()
    
    for (const [type, count] of Object.entries(categoryConfig) as [QuestionType, number][]) {
      const typeQuestions = ALL_QUESTIONS.filter(q => q.type === type)
      const shuffled = [...typeQuestions].sort(() => Math.random() - 0.5)
      
      for (let i = 0; i < count && i < shuffled.length; i++) {
        if (!usedIds.has(shuffled[i].id)) {
          const q = shuffled[i]
          
          // Shuffle options and update correctAnswer index
          if (q.options && q.options.length > 1) {
            const originalCorrect = q.options[q.correctAnswer]
            const shuffledOptions = [...q.options].sort(() => Math.random() - 0.5)
            const newCorrectIndex = shuffledOptions.indexOf(originalCorrect)
            questions.push({
              ...q,
              options: shuffledOptions,
              correctAnswer: newCorrectIndex
            })
          } else {
            questions.push(q)
          }
          
          usedIds.add(q.id)
        }
      }
    }
    
    return questions
  }

  const updateCategory = (type: QuestionType, delta: number) => {
    setCategoryConfig(prev => {
      const newValue = Math.max(0, Math.min(MAX_TOTAL_QUESTIONS, prev[type] + delta))
      const newTotal = Object.values(prev).reduce((a, b) => a + b, 0) - prev[type] + newValue
      
      if (newTotal > MAX_TOTAL_QUESTIONS && delta > 0) {
        return prev
      }
      
      return { ...prev, [type]: newValue }
    })
  }

  const saveResultMutation = useMutation({
    mutationFn: (result: { totalQuestions: number; correctAnswers: number; timeSpent: number; categoryScores: Record<string, number> }) => 
      intelligenceTestApi.saveResult({
        total_questions: result.totalQuestions,
        correct_answers: result.correctAnswers,
        time_spent: result.timeSpent,
        category_scores: result.categoryScores,
      }),
    onSuccess: () => {
      toast.success('Rezultat je sačuvan!')
    },
    onError: () => {
      toast.error('Greška pri čuvanju rezultata')
    }
  })

  const startTest = () => {
    const questions = generateQuestions()
    setSelectedQuestions(questions)
    setTestStarted(true)
    setStartTime(Date.now())
    setTimeLeft(questions[0]?.timeLimit || 30)
    setCurrentQuestion(0)
    setAnswers({})
  }

  const resetTest = () => {
    setCurrentQuestion(0)
    setAnswers({})
    setTimeLeft(30)
    setTestStarted(false)
    setTestCompleted(false)
    setStartTime(0)
    setSelectedQuestions([])
  }

  const handleAnswer = (answerIndex: number) => {
    const question = selectedQuestions[currentQuestion]
    
    setAnswers(prev => ({
      ...prev,
      [question.id]: answerIndex
    }))

    if (currentQuestion < selectedQuestions.length - 1) {
      setCurrentQuestion(prev => prev + 1)
      setTimeLeft(selectedQuestions[currentQuestion + 1]?.timeLimit || 30)
    } else {
      finishTest()
    }
  }

  const finishTest = () => {
    const endTime = Date.now()
    const totalTimeSpent = Math.floor((endTime - startTime) / 1000)
    
    const categoryScores: Record<string, { correct: number; total: number }> = {}
    let correctCount = 0

    selectedQuestions.forEach(q => {
      if (!categoryScores[q.type]) {
        categoryScores[q.type] = { correct: 0, total: 0 }
      }
      categoryScores[q.type].total++
      
      if (answers[q.id] === q.correctAnswer) {
        categoryScores[q.type].correct++
        correctCount++
      }
    })

    const result = {
      totalQuestions: selectedQuestions.length,
      correctAnswers: correctCount,
      timeSpent: totalTimeSpent,
      categoryScores: Object.fromEntries(
        Object.entries(categoryScores).map(([k, v]) => [k, Math.round((v.correct / v.total) * 100)])
      )
    }

    saveResultMutation.mutate(result)
    setTestCompleted(true)
  }

  const calculateIQ = (correct: number, timeSpent: number) => {
    const baseIQ = 100
    const correctBonus = (correct / selectedQuestions.length) * 40
    const timeEfficiency = Math.max(0, 1 - (timeSpent / (selectedQuestions.length * 30)))
    const timeBonus = timeEfficiency * 20
    
    return Math.min(160, Math.round(baseIQ + correctBonus + timeBonus))
  }

  const getIQCategory = (iq: number) => {
    if (iq >= 140) return { label: 'Genijalac', color: 'text-purple-600' }
    if (iq >= 130) return { label: 'Super inteligentan', color: 'text-indigo-600' }
    if (iq >= 120) return { label: 'Veoma inteligentan', color: 'text-blue-600' }
    if (iq >= 110) return { label: 'Inteligentan', color: 'text-green-600' }
    if (iq >= 90) return { label: 'Prosečan', color: 'text-yellow-600' }
    return { label: 'Ispod proseka', color: 'text-orange-600' }
  }

  if (!testStarted) {
    return (
      <div className="max-w-2xl mx-auto space-y-8 animate-fade-in">
        <div className="text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Testovi Sposobnosti</h1>
          <p className="text-gray-500 mt-2">
            Izaberi tip testa i testiraj svoje kognitivne sposobnosti
          </p>
        </div>

        <div className="card p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Konfiguracija testa
            </h2>
            <span className={clsx(
              'px-3 py-1 rounded-full text-sm font-medium',
              totalSelected > 0 && totalSelected <= MAX_TOTAL_QUESTIONS
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            )}>
              {totalSelected}/{MAX_TOTAL_QUESTIONS} pitanja
            </span>
          </div>

          <p className="text-sm text-gray-500">
            Izaberi broj pitanja za svaku kategoriju:
          </p>

          <div className="grid grid-cols-2 gap-4">
            {(Object.keys(TYPE_LABELS) as QuestionType[]).map((type) => (
              <div key={type} className={clsx(
                'p-4 rounded-xl bg-gradient-to-r text-white',
                TYPE_COLORS[type]
              )}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{TYPE_LABELS[type]}</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateCategory(type, -1)}
                      disabled={categoryConfig[type] <= 0}
                      className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 disabled:opacity-50 flex items-center justify-center"
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                    <span className="w-8 text-center font-bold text-lg">{categoryConfig[type]}</span>
                    <button
                      onClick={() => updateCategory(type, 1)}
                      disabled={categoryConfig[type] >= 10 || totalSelected >= MAX_TOTAL_QUESTIONS}
                      className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 disabled:opacity-50 flex items-center justify-center"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => {
              const newConfig = {
                spatial: Math.floor(Math.random() * 5) + 1,
                logical: Math.floor(Math.random() * 5) + 1,
                numerical: Math.floor(Math.random() * 5) + 1,
                verbal: Math.floor(Math.random() * 5) + 1,
                general: Math.floor(Math.random() * 5) + 1,
                flags: Math.floor(Math.random() * 5) + 1,
              }
              // Normalize to MAX_TOTAL_QUESTIONS
              const total = Object.values(newConfig).reduce((a, b) => a + b, 0)
              const scale = MAX_TOTAL_QUESTIONS / total
              setCategoryConfig({
                spatial: Math.round(newConfig.spatial * scale),
                logical: Math.round(newConfig.logical * scale),
                numerical: Math.round(newConfig.numerical * scale),
                verbal: Math.round(newConfig.verbal * scale),
                general: Math.round(newConfig.general * scale),
                flags: Math.round(newConfig.flags * scale),
              })
            }}
            className="w-full text-sm text-gray-500 hover:text-gray-700 py-2"
          >
            Nasumična konfiguracija
          </button>
        </div>

        <button
          onClick={startTest}
          disabled={totalSelected === 0}
          className="w-full btn-primary text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Brain className="w-6 h-6" />
          Započni test ({totalSelected} pitanja)
        </button>
      </div>
    )
  }

  if (testCompleted) {
    const correctCount = selectedQuestions.filter(q => answers[q.id] === q.correctAnswer).length
    const totalTime = Math.floor((Date.now() - startTime) / 1000)
    const iq = calculateIQ(correctCount, totalTime)
    const category = getIQCategory(iq)

    return (
      <div className="max-w-2xl mx-auto space-y-8 animate-fade-in">
        <div className="text-center">
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-yellow-400 to-amber-500 flex items-center justify-center">
            <Trophy className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Rezultat</h1>
          <p className="text-gray-500 mt-2">Završio si test inteligencije</p>
        </div>

        <div className="card p-8 text-center space-y-6">
          <div>
            <p className="text-sm text-gray-500 uppercase tracking-wide">Procenjeni IQ</p>
            <p className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              {iq}
            </p>
            <p className={clsx('text-lg font-semibold mt-2', category.color)}>
              {category.label}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-green-50">
              <p className="text-2xl font-bold text-green-600">{correctCount}/{selectedQuestions.length}</p>
              <p className="text-sm text-gray-600">Tačnih odgovora</p>
            </div>
            <div className="p-4 rounded-xl bg-blue-50">
              <p className="text-2xl font-bold text-blue-600">{totalTime}s</p>
              <p className="text-sm text-gray-600">Ukupno vreme</p>
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-sm text-gray-500">Rezultat po kategorijama:</p>
            <div className="grid grid-cols-2 gap-3">
              {(Object.keys(TYPE_LABELS) as QuestionType[]).map((type) => {
                const typeQuestions = selectedQuestions.filter(q => q.type === type)
                const typeCorrect = typeQuestions.filter(q => answers[q.id] === q.correctAnswer).length
                const percentage = typeQuestions.length > 0 ? Math.round((typeCorrect / typeQuestions.length) * 100) : 0
                
                return (
                  <div key={type} className={clsx(
                    'p-3 rounded-xl bg-gradient-to-r text-white text-sm',
                    TYPE_COLORS[type]
                  )}>
                    <div className="flex justify-between items-center">
                      <span>{TYPE_LABELS[type]}</span>
                      <span className="font-bold">{percentage}%</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={resetTest}
            className="flex-1 btn-secondary"
          >
            <RefreshCw className="w-5 h-5" />
            Novi test
          </button>
        </div>
      </div>
    )
  }

  const question = selectedQuestions[currentQuestion]
  const progress = ((currentQuestion + 1) / selectedQuestions.length) * 100

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Test Sposobnosti</h1>
          <p className="text-sm text-gray-500">
            Pitanje {currentQuestion + 1} od {selectedQuestions.length}
          </p>
        </div>
        <div className={clsx(
          'px-4 py-2 rounded-xl text-white font-bold',
          timeLeft <= 10 ? 'bg-red-500 animate-pulse' : 'bg-blue-500'
        )}>
          {timeLeft}s
        </div>
      </div>

      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className={clsx(
        'inline-flex items-center gap-2 px-4 py-2 rounded-full text-white text-sm font-medium',
        'bg-gradient-to-r ' + TYPE_COLORS[question.type]
      )}>
        {TYPE_LABELS[question.type]} pitanje
      </div>

      <div className="card p-8">
        {question.image && (
          <div className="mb-6 text-center">
            {(() => {
              const flagUrl = getFlagUrl(question.image, question.countryCode)
              if (flagUrl) {
                return (
                  <img 
                    src={flagUrl} 
                    alt="Zastava"
                    className="mx-auto h-48 object-contain rounded-lg shadow-md border border-gray-200"
                    onError={(e) => {
                      const img = e.target as HTMLImageElement
                      img.style.display = 'none'
                      const fallback = img.parentElement?.querySelector('.flag-fallback') as HTMLElement
                      if (fallback) fallback.style.display = 'inline'
                    }}
                  />
                )
              }
              return <span className="text-6xl">{question.image}</span>
            })()}
            <span className="flag-fallback text-6xl" style={{ display: 'none' }}>{question.image}</span>
          </div>
        )}
        <p className="text-xl font-semibold text-gray-900 mb-8">
          {question.question}
        </p>

        <div className="space-y-3">
          {question.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswer(index)}
              className={clsx(
                'w-full p-4 rounded-xl border-2 text-left font-medium transition-all',
                answers[question.id] === index
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                  : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
              )}
            >
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-200 text-gray-700 mr-3 text-sm font-bold">
                {String.fromCharCode(65 + index)}
              </span>
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => {
            if (currentQuestion > 0) {
              setCurrentQuestion(prev => prev - 1)
              setTimeLeft(selectedQuestions[currentQuestion - 1]?.timeLimit || 30)
            }
          }}
          disabled={currentQuestion === 0}
          className="btn-secondary disabled:opacity-50"
        >
          <ChevronLeft className="w-5 h-5" />
          Prethodno
        </button>

        <div className="flex gap-2">
          {selectedQuestions.map((_, idx) => (
            <div
              key={idx}
              className={clsx(
                'w-3 h-3 rounded-full',
                idx === currentQuestion ? 'bg-indigo-500' :
                answers[selectedQuestions[idx].id] !== undefined 
                  ? 'bg-green-500' 
                  : 'bg-gray-300'
              )}
            />
          ))}
        </div>

        <button
          onClick={() => handleAnswer(-1)}
          className="btn-secondary text-red-600"
        >
          Preskoči
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
