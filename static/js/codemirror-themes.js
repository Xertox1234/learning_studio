/**
 * CodeMirror 6 VS Code Dark Theme
 * Custom theme that mimics VS Code's dark theme
 */

import { EditorView } from "codemirror"
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language"
import { tags as t } from "@lezer/highlight"

// VS Code Dark color palette
const chalky = "#e5c07b",
      coral = "#e06c75", 
      cyan = "#56b6c2",
      invalid = "#ffffff",
      ivory = "#abb2bf",
      stone = "#7d8799",
      malibu = "#61afef", 
      sage = "#98c379",
      whiskey = "#d19a66",
      violet = "#c678dd",
      darkBackground = "#21252b",
      highlightBackground = "#2c313a",
      background = "#282c34",
      tooltipBackground = "#353a42",
      selection = "#3e4451",
      cursor = "#528bff"

// VS Code Dark theme configuration
export const vscodeDark = EditorView.theme({
  "&": {
    color: ivory,
    backgroundColor: background
  },

  ".cm-content": {
    caretColor: cursor,
    padding: "16px",
    minHeight: "200px",
    fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace",
    fontSize: "14px",
    lineHeight: "1.5"
  },

  ".cm-cursor, .cm-dropCursor": { borderLeftColor: cursor },
  ".cm-selectionBackground, .cm-focusRing, ::selection": { backgroundColor: selection },

  ".cm-panels": { backgroundColor: darkBackground, color: ivory },
  ".cm-panels.cm-panels-top": { borderBottom: "2px solid black" },
  ".cm-panels.cm-panels-bottom": { borderTop: "2px solid black" },

  ".cm-searchMatch": {
    backgroundColor: "#72a1ff59",
    outline: "1px solid #457dff"
  },
  ".cm-searchMatch.cm-searchMatch-selected": {
    backgroundColor: "#6199ff2f"
  },

  ".cm-activeLine": { backgroundColor: "#2c313c" },
  ".cm-selectionMatch": { backgroundColor: "#aafe661a" },

  "&.cm-focused .cm-matchingBracket, &.cm-focused .cm-nonmatchingBracket": {
    backgroundColor: "#bad0f847"
  },

  ".cm-gutters": {
    backgroundColor: background,
    color: stone,
    border: "none"
  },

  ".cm-activeLineGutter": {
    backgroundColor: highlightBackground
  },

  ".cm-foldPlaceholder": {
    backgroundColor: "transparent",
    border: "none",
    color: "#ddd"
  },

  ".cm-tooltip": {
    border: "none",
    backgroundColor: tooltipBackground
  },
  ".cm-tooltip .cm-tooltip-arrow:before": {
    borderTopColor: "transparent",
    borderBottomColor: "transparent"
  },
  ".cm-tooltip .cm-tooltip-arrow:after": {
    borderTopColor: tooltipBackground,
    borderBottomColor: tooltipBackground
  },
  ".cm-tooltip-autocomplete": {
    "& > ul > li[aria-selected]": {
      backgroundColor: highlightBackground,
      color: ivory
    }
  }
}, { dark: true })

// VS Code Dark syntax highlighting
export const vscodeHighlightStyle = HighlightStyle.define([
  { tag: t.keyword, color: violet },
  { tag: [t.name, t.deleted, t.character, t.propertyName, t.macroName], color: coral },
  { tag: [t.function(t.variableName), t.labelName], color: malibu },
  { tag: [t.color, t.constant(t.name), t.standard(t.name)], color: whiskey },
  { tag: [t.definition(t.name), t.separator], color: ivory },
  { tag: [t.typeName, t.className, t.number, t.changed, t.annotation, t.modifier, t.self, t.namespace], color: chalky },
  { tag: [t.operator, t.operatorKeyword, t.url, t.escape, t.regexp, t.link, t.special(t.string)], color: cyan },
  { tag: [t.meta, t.comment], color: stone },
  { tag: t.strong, fontWeight: "bold" },
  { tag: t.emphasis, fontStyle: "italic" },
  { tag: t.strikethrough, textDecoration: "line-through" },
  { tag: t.link, color: stone, textDecoration: "underline" },
  { tag: t.heading, fontWeight: "bold", color: coral },
  { tag: [t.atom, t.bool, t.special(t.variableName)], color: whiskey },
  { tag: [t.processingInstruction, t.string, t.inserted], color: sage },
  { tag: t.invalid, color: invalid },
])

// Combined extension for VS Code Dark theme
export const vscodeTheme = [
  vscodeDark,
  syntaxHighlighting(vscodeHighlightStyle)
]