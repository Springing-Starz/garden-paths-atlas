import { archiveExtensions, documentExtension } from '@/lib/document-formats';
const pdf = { url: '/__l5e/assets-v1/dfdbda03-3ce9-4dfc-911a-6b95d0d837d1/e3f2c139-pdf.webp' };
const word = { url: '/__l5e/assets-v1/8a50caf7-d309-4601-8929-ab2adc9ee925/cd164d7b-word.webp' };
const excel = { url: '/__l5e/assets-v1/497117d8-af4b-4a78-a153-c11065027ae4/76c3c917-excel.webp' };
const powerpoint = { url: '/__l5e/assets-v1/c9cc0a1f-e5e0-4fc9-92dc-3b234e99ecac/995dbb07-powerpoint.webp' };
const archive = { url: '/__l5e/assets-v1/e3d56678-c9bd-42c2-a4e6-7af7f0b0d178/e3e38388-archive.webp' };
const rtf = { url: '/__l5e/assets-v1/25ac24a3-bc03-4901-96db-32b32cd9969b/03dc7ab4-rtf.png' };
const txt = { url: '/__l5e/assets-v1/6943fdd1-013b-4e12-879e-ce9c686ca922/cd7794b8-txt.webp' };

const placeholders = { pdf, word, excel, powerpoint, archive, rtf, txt };

export function documentPlaceholder(url: string) {
  const extension = documentExtension(url);
  if (extension === 'pdf') return placeholders.pdf;
  if (['doc', 'docx'].includes(extension)) return placeholders.word;
  if (['xls', 'xlsx'].includes(extension)) return placeholders.excel;
  if (['ppt', 'pptx', 'pps', 'ppsx'].includes(extension)) return placeholders.powerpoint;
  if (extension === 'rtf') return placeholders.rtf;
  if (extension === 'txt') return placeholders.txt;
  if (archiveExtensions.includes(extension)) return placeholders.archive;
  return null;
}
