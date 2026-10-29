// Hash routes keep collection links refreshable with the local FastAPI server.
export function readRoute(hash = window.location.hash) {
  const path = hash.replace(/^#/, '') || '/';
  if (path === '/') return {page:'home'};
  if (path === '/watched') return {page:'watched'};
  if (path === '/genres') return {page:'genres'};
  if (path === '/lab') return {page:'lab'};
  if (path === '/collection/recommended') return {page:'collection',concept:'recommended'};
  if (path === '/collection/saved') return {page:'collection',concept:'saved'};
  if (path === '/collection/watch-again') return {page:'collection',concept:'watch-again'};
  if (path.startsWith('/collection/genre/')) {
    try {
      const genre=decodeURIComponent(path.slice('/collection/genre/'.length));
      if (genre && genre.length <= 40) return {page:'collection',concept:'genre',genre};
    } catch { /* An invalid deep link falls through to the useful error page. */ }
  }
  return {page:'not-found'};
}

export function watchAgain(profile) {
  return profile.filter(movie=>movie.rating>=3.5).slice()
    .sort((a,b)=>b.rating-a.rating || (b.watchedAt||0)-(a.watchedAt||0))
    .map(movie=>({...movie,reason:`You rated this ${movie.rating} out of 5`}));
}

export function collectionInfo(route) {
  if (route.concept==='saved') return {title:'Saved movies',description:'Good films, kept for a future movie night.'};
  if (route.concept==='watch-again') return {title:'Watch again',description:'Your highest-rated watched films, ready for another look.'};
  if (route.concept==='genre') return {title:`${route.genre} movies`,description:`A full collection of ${route.genre} films, matched to your taste.`};
  return {title:'Movies you might like',description:'Recommendations shaped by your watched movies and favorite genres.'};
}
