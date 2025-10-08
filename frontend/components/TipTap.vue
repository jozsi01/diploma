<template>
  <div class="buttons">
    <button class="manageButtons" @click="editor.chain().focus().toggleBold().run()">
      <Bold :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleItalic().run()">
      <Italic :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleStrike().run()">
      <Strikethrough :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleCode().run()"><Code :size="16" /></button>
    <button class="manageButtons" @click="editor.chain().focus().setParagraph().run()">
      <Pilcrow :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleHeading({ level: 1 }).run()">
      <Heading1 :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()">
      <Heading2 :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()">
      <Heading3 :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleBulletList().run()">
      <List :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleOrderedList().run()">
      <ListOrdered :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().setHorizontalRule().run()">
      <Minus :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().toggleUnderline().run()">
      <Underline :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().undo().run()">
      <Undo :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().redo().run()">
      <Redo :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().setTextAlign('left').run()">
      <TextAlignStart :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().setTextAlign('center').run()">
      <TextAlignCenter :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().setTextAlign('right').run()">
      <TextAlignEnd :size="16" />
    </button>
    <button class="manageButtons" @click="editor.chain().focus().setTextAlign('justify').run()">
      <TextAlignJustify :size="16" />
    </button>

  </div>
  <div>
    <EditorContent class="editor__content" :editor="editor" />
  </div>
  <button class="manageButtons" @click="saveHtml">
    <Save :size="16" />
  </button>
</template>

<script setup>
import { useEditor } from '@tiptap/vue-3'
import { EditorContent } from '@tiptap/vue-3'
import { Bold, Italic, Heading1, Heading2, Heading3, Strikethrough, Underline, List, ListOrdered, Undo, Redo, Code, Pilcrow, Minus, Save, TextAlignStart, TextAlignCenter, TextAlignEnd, TextAlignJustify } from 'lucide-vue-next';
import StarterKit from '@tiptap/starter-kit'
import TextAlign from '@tiptap/extension-text-align'
import { TableKit } from '@tiptap/extension-table'
import { onMounted } from 'vue';

const props = defineProps({
  document_id: String,
})


async function editDocument() {
    try{
        const resp = await fetch(`/api/documents/${props.document_id}/html`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (resp.ok) {
            const data = await resp.text();
            editor.value.commands.setContent(data);
            console.log('HTML content fetched:', data);
            
        } else if (resp.status === 401) {
            console.error('Unauthorized access - please log in');
        }
    } catch (error) {
        console.error('Error fetching HTML content:', error);
    }
}

async function saveHtml() {
  const html = editor.value.getHTML();
  try {
    const resp = await fetch(`/api/documents/${props.document_id}/save`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ "html":html }),
    });
    if (resp.ok) {
      console.log('Document saved successfully');
    } else {
      console.error('Failed to save document');
    }
  } catch (error) {
    console.error('Error saving document:', error);
  }
}

onMounted(() => {
  editDocument();
});

const editor = useEditor({
  content: "Hello world!",
  extensions: [
    StarterKit.configure({
      paragraph: {
        HTMLAttributes: {
          class: 'my-custom-paragraph',
        },
      },
    }),
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    TableKit.configure({
      resizable: true,
      cellMinWidth: 60,
    }),
  ],
  editable: true,
  onUpdate: ({ editor }) => {
    console.log('Content updated:')
  },
})

</script>

<style scoped>
.manageButtons {
  background-color: transparent;
  border: 1px solid black;
  border-radius: 3px;
  cursor: pointer;
  margin: 2px;
}

:deep(.editor__content) table td,
:deep(.editor__content) table th {
  min-width: 1em;
  border: 2px solid #ddd;
  vertical-align: top;
  box-sizing: border-box;
  position: relative;
}

:global(.editor__content) {

  min-height: 150px;
  font-family: Arial, sans-serif;
  font-size: 16px;
  max-height: 70vh;
  /* or any fixed value like 400px */
  overflow-y: auto;

}

:deep(.my-custom-paragraph) {
  margin-left: 10px;
}

:global(.editor__content) p {
  font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;

}
</style>