document.addEventListener('DOMContentLoaded', function(){
  const pageRoot = document.querySelector('main[data-publish-url][data-delete-url]');
  const searchInput = document.getElementById('draft-search');
  const sortSelect = document.getElementById('draft-sort');
  const categorySelect = document.getElementById('draft-category');
  const list = Array.from(document.querySelectorAll('.draft-card-wrapper'));
  const paginationEl = document.getElementById('draft-pagination');
  const messageWrap = document.getElementById('draft-action-messages');
  const pageSize = 6;
  let currentPage = 1;

  function getCookie(name) {
    const value = '; ' + document.cookie;
    const parts = value.split('; ' + name + '=');
    if (parts.length === 2) {
      return decodeURIComponent(parts.pop().split(';').shift());
    }
    return null;
  }

  function getCsrfToken(){
    const cookieToken = getCookie('csrftoken');
    if (cookieToken) return cookieToken;
    return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || null;
  }

  function showMessage(type, text){
    if(!messageWrap) return;
    const cls = type === 'success' ? 'alert-success' : (type === 'error' ? 'alert-danger' : 'alert-info');
    const icon = type === 'success' ? 'bi-check-circle-fill' : (type === 'error' ? 'bi-exclamation-triangle-fill' : 'bi-info-circle-fill');
    const node = document.createElement('div');
    node.className = 'alert '+cls+' alert-dismissible fade show action-message';
    node.role = 'alert';
    node.innerHTML = '<i class="bi '+icon+' me-2"></i>' + text + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    messageWrap.appendChild(node);
    window.setTimeout(()=>{
      if(node && node.parentNode){
        node.classList.remove('show');
        node.classList.add('hide');
        setTimeout(()=> node.remove(), 200);
      }
    }, 2600);
  }

  function renderPage(items, page){
    const start = (page-1)*pageSize;
    const end = start + pageSize;
    list.forEach((el, idx)=> el.style.display = (items.indexOf(el)>=start && items.indexOf(el)<end)?'flex':'none');
    renderPagination(items.length);
  }

  function renderPagination(totalItems){
     if(!paginationEl) return;
     const pages = Math.max(1, Math.ceil(totalItems/pageSize));
     paginationEl.innerHTML='';
    for(let i=1;i<=pages;i++){
      const li = document.createElement('li'); li.className='page-item'+(i===currentPage?' active':'');
      const a = document.createElement('a'); a.className='page-link'; a.href='#'; a.innerText=i;
      a.addEventListener('click', (e)=>{e.preventDefault(); currentPage=i; applyFilters();});
      li.appendChild(a); paginationEl.appendChild(li);
    }
  }

  function applyFilters(){
    const q = (searchInput.value||'').toLowerCase();
    const cat = categorySelect?categorySelect.value:'all';
    const sort = sortSelect?sortSelect.value:'all';

    let items = list.filter(el=>{
      if(q && !el.dataset.title.includes(q)) return false;
      if(cat && cat!=='all' && el.dataset.category !== cat) return false;
      return true;
    });

    if(sort==='recent'){
      items.sort((a,b)=> new Date(b.dataset.updated) - new Date(a.dataset.updated));
    } else if(sort==='oldest'){
      items.sort((a,b)=> new Date(a.dataset.updated) - new Date(b.dataset.updated));
    }

    // reorder DOM to match items order
    const parent = document.getElementById('draft-list');
    if(parent){
      items.forEach(it=> parent.appendChild(it));
    }
    renderPage(items, currentPage);
    return items.length;
  }

  if(searchInput) {
    searchInput.addEventListener('input', ()=>{ 
      currentPage=1; 
      const count = applyFilters();
      showMessage('info', 'Search completed. '+count+' draft(s) found.');
    });
  }
  if(sortSelect) {
    sortSelect.addEventListener('change', ()=>{ 
      currentPage=1; 
      const count = applyFilters();
      showMessage('success', 'Sort applied successfully. '+count+' draft(s) visible.');
    });
  }
  if(categorySelect) {
    categorySelect.addEventListener('change', ()=>{ 
      currentPage=1; 
      const count = applyFilters();
      showMessage('success', 'Category filter applied. '+count+' draft(s) visible.');
    });
  }

  // navigation actions
  document.querySelectorAll('.create-draft-btn').forEach(btn=>{
    btn.addEventListener('click', ()=> showMessage('success', 'Opening new draft editor...'));
  });
  document.querySelectorAll('.edit-draft-btn').forEach(btn=>{
    btn.addEventListener('click', ()=> showMessage('success', 'Opening draft "'+(btn.dataset.title || '')+'" for editing.'));
  });
  document.querySelectorAll('.continue-draft-btn').forEach(btn=>{
    btn.addEventListener('click', ()=> showMessage('success', 'Continuing draft "'+(btn.dataset.title || '')+'".'));
  });

  // preview buttons
  document.querySelectorAll('.preview-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const title = btn.dataset.title||'Preview';
      const content = btn.dataset.content||'';
      document.getElementById('previewModalTitle').innerText = title;
      document.getElementById('previewModalBody').innerHTML = '<div>'+content+'</div>';
      const editLink = document.getElementById('previewEditLink');
      editLink.href = '/upload_blog/'+btn.dataset.blogid+'/';
      const modal = new bootstrap.Modal(document.getElementById('draftPreviewModal'));
      modal.show();
      showMessage('success', 'Preview opened successfully for "'+title+'".');
    });
  });

  // delete confirmation
  document.querySelectorAll('.delete-btn').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const id = btn.dataset.id;
      const title = btn.dataset.title || 'selected draft';
      if(!confirm('Are you sure you want to delete this draft? This action cannot be undone.')) {
        showMessage('info', 'Delete action cancelled.');
        return;
      }
      // perform POST to delete endpoint (backend needs to implement)
      const csrf = getCsrfToken();
      const deleteUrl = pageRoot?.dataset.deleteUrl || '/doctor_delete_draft/';
      if(!csrf){
        showMessage('error', 'Delete failed. Missing CSRF token. Please reload the page.');
        return;
      }
      try{
        const res = await fetch(deleteUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/x-www-form-urlencoded','X-CSRFToken':csrf},body:new URLSearchParams({id:id})});
        if(res.ok){
          // remove card from DOM
          const el = document.querySelector('.delete-btn[data-id="'+id+'"]')?.closest('.draft-card-wrapper');
          if(el) el.remove();
          applyFilters();
          showMessage('success', 'Draft "'+title+'" deleted successfully.');
        } else {
          showMessage('error', 'Delete failed. Server responded with status '+res.status+'.');
        }
      }catch(e){ 
        console.error(e); 
        showMessage('error', 'Delete failed due to a network/server error.');
      }
    });
  });

  // publish action (frontend only) - placeholder
  document.querySelectorAll('.publish-btn').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const id = btn.dataset.id;
      const title = btn.dataset.title || 'selected draft';
      if(!confirm('Publish this draft now?')) {
        showMessage('info', 'Publish action cancelled.');
        return;
      }
      const csrf = getCsrfToken();
      const publishUrl = pageRoot?.dataset.publishUrl || '/doctor_publish_draft/';
      if(!csrf){
        showMessage('error', 'Publish failed. Missing CSRF token. Please reload the page.');
        return;
      }
      try{
        const res = await fetch(publishUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/x-www-form-urlencoded','X-CSRFToken':csrf},body:new URLSearchParams({id:id})});
        if(res.ok){
          showMessage('success', 'Draft "'+title+'" published successfully.');
          // optionally remove or update badge
        } else {
          showMessage('error', 'Publish failed. Server responded with status '+res.status+'.');
        }
      }catch(e){ 
        console.error(e);
        showMessage('error', 'Publish failed due to a network/server error.');
      }
    });
  });

  // initialize
  const initialCount = applyFilters();
  showMessage('info', 'Draft page loaded. '+initialCount+' draft(s) available.');
});
