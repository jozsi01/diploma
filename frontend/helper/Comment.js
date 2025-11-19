import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import Commment from '../components/Comment.vue'
import customAxios from './axios'

export default Node.create({
  name: 'comment',

  group: 'inline',
  inline: true,
  content: 'text*',
  marks: '_',


  addAttributes() {
      return {
        'comment-id': {
          default: '',
        },
      }
    },


  parseHTML() {
    return [
      {
        tag: 'comment',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'comment',
      mergeAttributes(HTMLAttributes, {
        class: 'comment-node',
      }),
      0, // 👈 VERY important: renders inner text
    ]
  },

  addNodeView() {
    return VueNodeViewRenderer(Commment)
  },

  addCommands() {
    return {
      setComment: (comment_id) => async ({ state }) => {
        const { from, to } = state.selection
        const slice = state.doc.slice(from, to) // keep formatting
       
        const tr = state.tr.replaceSelectionWith(
          state.schema.nodes.comment.create({'comment-id': comment_id}, slice.content),
          true
        )

        state.apply(tr)
        return true
      },
    }
  },
})