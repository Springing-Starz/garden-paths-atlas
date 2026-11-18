import { archiveExtensions, documentExtension } from '@/lib/document-formats';
const pdf = { url: '/__l5e/assets-v1/9ffc31ca-31de-4044-822c-fadec202b1f0/e3f2c139-pdf.webp' };
const word = { url: '/__l5e/assets-v1/c03297cd-10d1-44a8-983d-02681bb3ec23/cd164d7b-word.webp' };
const excel = { url: '/__l5e/assets-v1/f9b497fe-481e-4f0e-84a4-e540fa0f7c0b/76c3c917-excel.webp' };
const powerpoint = { url: '/__l5e/assets-v1/525d87f3-4fa1-47de-b20f-c60280748252/995dbb07-powerpoint.webp' };
const archive = { url: '/__l5e/assets-v1/18e09123-8cf3-47a0-9713-260d69da7700/e3e38388-archive.webp' };
const rtf = { url: '/__l5e/assets-v1/114ea74f-b05e-4880-83dd-9c5fd2f8d90d/03dc7ab4-rtf.png' };
const txt = { url: '/__l5e/assets-v1/897de3a5-1580-463f-a775-3a3c67b4146a/cd7794b8-txt.webp' };

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
