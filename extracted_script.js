<USER_REQUEST>
 · JS
Copy

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageBreak, VerticalAlign
} = require('docx');
const fs = require('fs');
 
const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
 
function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, size: 32, color: "1F3864", font: "Arial" })],
    spacing: { before: 400, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "2E75B6", space: 1 } }
  });
}
 
function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, size: 26, color: "2E75B6", font: "Arial" })],
    spacing: { before: 300, after: 120 }
  });
}
 
function qLabel(text) {
<truncated 124359 bytes>