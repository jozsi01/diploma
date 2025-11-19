import axios from 'axios';


 const customAxios  = axios.create({
    baseURL: '/api',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },

});

customAxios.interceptors.response.use(undefined,(error)=>{
    if (error.response.status === 401) {
        window.location.href = '/auth';
    }
    return Promise.reject(error);
})

export default customAxios;
    