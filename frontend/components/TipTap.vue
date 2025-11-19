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
  <div class="persistButtons">
    <button class="manageButtons" @click="saveHtml">
      <Save :size="32" />
    </button>
    <button class="manageButtons" @click="exportDocument">
      <FileType :size="32" />
    </button>


  </div>
  <BubbleMenu v-if="editor" :editor="editor" :options="{ placement: 'right', offset: 8, onHide: hideCommentInput }">
    <div class="bubbleMenu" v-if="!showCommentInput">
      <MessageCircleMore @click="showCommentInput = true" />
    </div>
    <div class="bubbleCommentInput" v-if="showCommentInput">
      <h5>Add Comment</h5>
      <input v-model="commentContent" type="text" placeholder="Type your comment..." />
      <button @click="addComment">Add</button>
    </div>
  </BubbleMenu>

</template>

<script setup>
import { useEditor } from '@tiptap/vue-3'
import { EditorContent } from '@tiptap/vue-3'
import { Bold, MessageCircleMore, FileType, Italic, Heading1, Heading2, Heading3, Strikethrough, Underline, List, ListOrdered, Undo, Redo, Code, Pilcrow, Minus, Save, TextAlignStart, TextAlignCenter, TextAlignEnd, TextAlignJustify } from 'lucide-vue-next';
import StarterKit from '@tiptap/starter-kit'
import TextAlign from '@tiptap/extension-text-align'
import { TableKit } from '@tiptap/extension-table'
import { onBeforeUnmount, onMounted, onUnmounted, watch } from 'vue';
import customAxios from '../helper/axios';
import { BubbleMenu } from '@tiptap/vue-3/menus'
import { useStore } from '../store/store.js';
import Comment from '../helper/Comment.js'
import { ref } from 'vue';
import Image from '@tiptap/extension-image';

const store = useStore();
const props = defineProps({
  document_id: String,
})
const showCommentInput = ref(false);
const commentContent = ref("");
const emit = defineEmits(["comment-clicked"])

function hideCommentInput() {
  showCommentInput.value = false;
  commentContent.value = "";
}

async function exportDocument() {
  try {
    const html = editor.value.getHTML();

    const { data } = await customAxios.put(`/documents/${props.document_id}/docx`, {
      html: html,
    });



    console.log('Document exported successfully');
    console.log(data);
  } catch (error) {
    console.error('Error exporting document:', error);
  }
}

async function editDocument() {
  try {
    const { data } = await customAxios.get(`/documents/${props.document_id}/html`, {
      responseType: 'text', // ensure we get raw HTML text
    });

    editor.value.commands.setContent(data);
    console.log('HTML content fetched:', data);
  } catch (error) {
    console.error('Error fetching HTML content:', error);
  }
}

async function saveHtml() {
  const html = editor.value.getHTML();

  try {
    const resp = await customAxios.put(`/documents/${props.document_id}/save`, { html });
    console.log(resp)
    if (resp.status === 200) {
      alert('Document saved successfully!');
    } else {
      alert('Failed to save document.');
    }
  } catch (error) {
    console.error('Error saving document:', error);
  }
}

async function checkOwnership() {
  try {
    const { data } = await customAxios.get(`/isOwner/${props.document_id}`);
    console.log("Ownership data: ", data);
    if (!data.is_owner) {
      editor.value.view.dom.addEventListener('keydown', (e) => {
        e.preventDefault();
        return false
      })
    }
  } catch (error) {
    console.error('Error checking document ownership:', error);
  }
}

onMounted(async () => {
  await editDocument();
  await checkOwnership();
  console.log("editor: ", editor.value)
});
onBeforeUnmount(() => {
  if (editor.value) {

    editor.value.view.dom.removeEventListener('keydown', e => e.preventDefault())
  }
});



onUnmounted(() => {
  if (editor.value) {
    editor.value.destroy();
  }
});

async function addComment() {
  const { data } = await customAxios.post('/comments', {
    document_id: props.document_id,
    content: commentContent.value,

  })
  editor.value.chain().focus().setComment(data.comment_id).run()
  try{
    await customAxios.put('/comments/save', {
    document_id: props.document_id,
    html_content: editor.value.getHTML(),
  })
  } catch (error) {
    console.error("Error saving comment:", error)
  }
   try {
    customAxios.get('/comments/' + props.document_id).then((response) => {
      if (response.status === 200) {
        store.comments = response.data
        console.log('Fetched comments after adding new comment:', store.comments)
      }
    })
  } catch (error) {
    console.error('Error fetching comments:', error)
  }
}




const editor = useEditor({
  content: "Hello world!",
  editable: true,
  extensions: [
    StarterKit.configure({
      editable: false,
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
    Image.configure({
      inline: true
    }),
    Comment,


  ],
  onUpdate: ({ editor }) => {
    console.log('Content updated:', editor.getHTML());
  },
})

watch(editor, (newEditor) => {
  if (newEditor) {
    newEditor.on('comment-clicked', (comment) => {
      emit('comment-clicked', comment);
    })
  }
})
watch(() => store.selectedCommentId, (newId) => {
  if (!editor.value || !newId) return;
  if (newId.from === "editor") return;
  let targetPos = null;


  // 1️⃣ Find the node position in the ProseMirror document
  editor.value.state.doc.descendants((node, pos) => {
    if (node.type.name === 'comment' && node.attrs['comment-id'] === newId.id) {
      targetPos = pos;
      return false; // stop after first match
    }
  });

  if (targetPos === null) {
    return;
  }

  // 2️⃣ Get the DOM node rendered by ProseMirror for that position
  const dom = editor.value.view.nodeDOM(targetPos);

  if (dom && dom.scrollIntoView) {
    // 3️⃣ Use native DOM smooth scrolling
    dom.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } else {
    console.warn('No DOM element found for comment node.');
  }
})

</script>

<style scoped>
.bubbleCommentInput {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid #ddd;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 10px 12px;
  width: 240px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bubbleCommentInput h5 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 4px;
}

.bubbleCommentInput input {
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.bubbleCommentInput input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
}

.bubbleCommentInput button {
  align-self: flex-end;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.bubbleCommentInput button:hover {
  background-color: #2563eb;
}

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

.bubbleMenu {
  display: flex;
  padding: 5px;
  background-color: rgb(253, 253, 253);
  border-color: grey;
  border-radius: 5px;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
}

.bubbleMenu:hover {
  cursor: pointer;
  background-color: #e0e0e0;
}

.persistButtons {
  display: flex;
  justify-content: flex-end;
}

:deep(.editor__content) {

  font-family: Arial, sans-serif;
  font-size: 16px;
  max-height: 70vh;
  border: 1px solid gray;
  /* or any fixed value like 400px */
  overflow-y: auto;

}
</style>