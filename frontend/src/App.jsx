import React, {useEffect, useMemo, useRef, useState} from 'react';
import {ArrowLeft, ArrowRight, ArrowUpRight, Bookmark, Check, ChevronLeft, ChevronRight, Compass, FlaskConical, Heart, History, LoaderCircle, Plus, Search, SlidersHorizontal, Sparkles, Star, X} from 'lucide-react';
import {api, stored, ClapperboardArt, MoviePoster, MovieCard} from './components.jsx';
import {collectionInfo, readRoute, watchAgain} from './library.js';

const genreHref = genre => `#/collection/genre/${encodeURIComponent(genre)}`;
const ratingsFor = profile => profile.map(({movieId,rating})=>({movieId,rating}));

function EmptyState({title,children,href,label}) {
  return <div className="empty-state"><Bookmark size={26}/><h3>{title}</h3><p>{children}</p>{href && <a className="text-link" href={href}>{label}<ArrowUpRight size={14}/></a>}</div>;
}

function Shelf({title,subtitle,movies,href,empty,emptyHref,emptyLabel,cardProps}) {
  const track=useRef(null);
  const [edges,setEdges]=useState({left:false,right:false});
  useEffect(()=>{
    const element=track.current;
    const measure=()=>setEdges({left:element.scrollLeft>3,right:element.scrollLeft+element.clientWidth<element.scrollWidth-3});
    measure();
    element.addEventListener('scroll',measure,{passive:true});
    const resize=new ResizeObserver(measure); resize.observe(element);
    return ()=>{element.removeEventListener('scroll',measure);resize.disconnect();};
  },[movies.length]);
  const scroll=direction=>track.current.scrollBy({left:direction*track.current.clientWidth*.8,
    behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
  return <section className="movie-shelf" aria-label={title}>
    <div className="shelf-heading"><div><h2>{title}</h2><p>{subtitle}</p></div><div className="shelf-actions"><a href={href} aria-label={`Open ${title} collection`}>See more<ArrowUpRight size={13}/></a><button aria-label={`Scroll ${title} left`} disabled={!edges.left} onClick={()=>scroll(-1)}><ChevronLeft size={18}/></button><button aria-label={`Scroll ${title} right`} disabled={!edges.right} onClick={()=>scroll(1)}><ChevronRight size={18}/></button></div></div>
    <div className="movie-row-track" ref={track} tabIndex={0} aria-label={`${title} movie row`}>
      {movies.slice(0,10).map(movie=><div className="shelf-cell" key={movie.movieId}><MovieCard movie={movie} {...cardProps(movie)}/></div>)}
      {movies.length===0 && <div className="shelf-empty"><Bookmark size={28}/><strong>Nothing here yet</strong><p>{empty}</p>{emptyHref && <a href={emptyHref}>{emptyLabel}<ArrowUpRight size={14}/></a>}</div>}
      <a className="row-see-more" href={href} aria-label={`See more ${title}`}><span><ArrowRight size={28}/></span><strong>See more</strong><small>{title}</small></a>
    </div>
  </section>;
}

function GenreSettings({stats,favorites,onToggle,onClear}) {
  return <section className="genre-settings"><div className="page-eyebrow"><Heart size={15}/> MAKE IT YOURS</div><h1>Your favorite genres.</h1><p className="page-intro">Choose up to five. Home will follow these genres, or your most-watched genres when you leave them blank.</p><fieldset className="favorite-genres"><legend>Your genres</legend><div className="favorite-genres-heading"><p>{favorites.length}/5 selected · saved in this browser</p>{favorites.length>0 && <button onClick={onClear}>Clear favorites</button>}</div><div className="favorite-genre-options">{stats?.genres.map(genre=><button key={genre} className={favorites.includes(genre)?'chosen':''} aria-label={`Favorite genre: ${genre}`} aria-pressed={favorites.includes(genre)} disabled={!favorites.includes(genre)&&favorites.length>=5} onClick={()=>onToggle(genre)}>{favorites.includes(genre)?<Check size={13}/>:<Plus size={13}/>} {genre}</button>)}</div></fieldset><a className="hero-link" href="#/">Back to your home<ArrowRight size={17}/></a></section>;
}

function WatchedPage({profile,onAdd,onRate,onRemove,onDemo,stats}) {
  const [query,setQuery]=useState('');
  const [results,setResults]=useState([]);
  const [searching,setSearching]=useState(false);
  const [error,setError]=useState('');
  useEffect(()=>{
    if (!query.trim()) {setResults([]);setSearching(false);return;}
    const controller=new AbortController();setSearching(true);setError('');
    const timer=setTimeout(()=>api(`/movies?q=${encodeURIComponent(query)}&limit=8`,{signal:controller.signal})
      .then(data=>setResults(data.movies)).catch(e=>{if(e.name!=='AbortError')setError(e.message);})
      .finally(()=>{if(!controller.signal.aborted)setSearching(false);}),220);
    return ()=>{clearTimeout(timer);controller.abort();};
  },[query]);
  const add=movie=>{onAdd(movie);setQuery('');};
  return <section className="watched-page"><div className="page-eyebrow"><History size={15}/> YOUR VIEWING HISTORY</div><h1>Your watched movies.</h1><p className="page-intro">Add the films you’ve seen and tell us what you thought. Your history shapes the recommendations on Home.</p><div className="watched-layout"><div className="watched-editor"><div className="search-area"><Search size={18}/><input aria-label="Search watched movies" placeholder="Add a movie you’ve watched…" value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Escape')setQuery('');}}/>{searching?<LoaderCircle size={17} className="spin"/>:query&&<button aria-label="Clear search" onClick={()=>setQuery('')}><X size={17}/></button>}
      {query.trim()&&<div className="search-results" role="region" aria-label="Movie search results">{searching?<p>Searching the collection…</p>:results.length?results.map(movie=><button key={movie.movieId} onClick={()=>add(movie)} disabled={profile.some(item=>item.movieId===movie.movieId)}><MoviePoster movie={movie} thumbnail/><span><strong>{movie.title}</strong><small>{movie.genres.join(' · ')}</small></span>{profile.some(item=>item.movieId===movie.movieId)?<Check size={16}/>:<Plus size={16}/>}</button>):<p>No films found. Try another title.</p>}</div>}
    </div>{error&&<p role="alert" className="inline-error">{error}</p>}<div className="history-heading"><h2>{profile.length} watched {profile.length===1?'movie':'movies'}</h2><span>Rate 4–5 stars to add a film to Watch again.</span></div><div className="profile-list">{profile.length?profile.slice().reverse().map(movie=><div className="profile-row" key={movie.movieId}><MoviePoster movie={movie} thumbnail/><div className="profile-name"><strong>{movie.title.replace(/\s*\(\d{4}\)\s*$/,'')}</strong><small>{movie.year} · {movie.genres?.slice(0,3).join(' / ')}</small></div><div className="stars" aria-label={`Rate ${movie.title}`}>{[1,2,3,4,5].map(rating=><button key={rating} aria-label={`Rate ${movie.title} ${rating} stars`} aria-pressed={movie.rating===rating} onClick={()=>onRate(movie.movieId,rating)}><Star size={16} fill={movie.rating>=rating?'currentColor':'none'}/></button>)}</div><button className="remove-pick" aria-label={`Remove ${movie.title} from watched movies`} onClick={()=>onRemove(movie.movieId)}><X size={16}/></button></div>):<EmptyState title="Every good recommendation starts somewhere.">Search above to add your first watched film, or <button className="text-link" onClick={onDemo}>try a sci-fi profile<ArrowUpRight size={13}/></button>.</EmptyState>}</div></div><aside className="history-note"><Sparkles size={23}/><h3>A little history.<br/>Better discoveries.</h3><p>We count the genres of your watched films to build your home rows when you haven’t chosen favorites.</p><a href="#/genres">Choose favorite genres<ArrowUpRight size={14}/></a><small>{stats?.movies.toLocaleString()||'Thousands of'} movies to explore</small></aside></div></section>;
}

function CollectionPage({route,profile,favorites,watchlist,cardProps,stats}) {
  const info=collectionInfo(route);
  const local=route.concept==='saved'||route.concept==='watch-again';
  const localMovies=useMemo(()=>route.concept==='saved'?watchlist.map(movie=>({...movie,reason:undefined})):watchAgain(profile),[route.concept,watchlist,profile]);
  const [movies,setMovies]=useState([]);
  const [offset,setOffset]=useState(0);
  const [hasMore,setHasMore]=useState(false);
  const [busy,setBusy]=useState(!local);
  const [loadingMore,setLoadingMore]=useState(false);
  const [error,setError]=useState('');
  const [moreError,setMoreError]=useState('');
  const [localCount,setLocalCount]=useState(24);
  const [showFilters,setShowFilters]=useState(false);
  const [filterGenre,setFilterGenre]=useState('');
  const [era,setEra]=useState('');
  const [mode,setMode]=useState('hybrid');
  const [diversity,setDiversity]=useState(.15);
  const [retry,setRetry]=useState(0);
  const generation=useRef(0),moreRequest=useRef(null);
  const request=(nextOffset,signal)=>{
    const years=era==='classic'?{year_max:1999}:era==='2000'?{year_min:2000,year_max:2009}:era==='2010'?{year_min:2010}:{};
    return api('/recommend',{method:'POST',headers:{'Content-Type':'application/json'},signal,
      body:JSON.stringify({ratings:ratingsFor(profile),favorite_genres:favorites,k:24,offset:nextOffset,
        genre:route.concept==='genre'?route.genre:filterGenre||null,mode,diversity,...years})});
  };
  useEffect(()=>{
    if(local)return;
    const controller=new AbortController();generation.current+=1;
    moreRequest.current?.abort();moreRequest.current=null;setLoadingMore(false);setMoreError('');
    setBusy(true);setError('');setHasMore(false);setMovies([]);
    request(0,controller.signal).then(data=>{setMovies(data.recommendations);setOffset(data.nextOffset);setHasMore(data.hasMore);})
      .catch(e=>{if(e.name!=='AbortError')setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});
    return ()=>controller.abort();
  },[profile,favorites,route.concept,route.genre,filterGenre,era,mode,diversity,retry,local]);
  useEffect(()=>()=>moreRequest.current?.abort(),[]);
  const loadMore=async()=>{
    if(local){setLocalCount(count=>count+24);return;}
    if(busy||loadingMore||moreRequest.current||!hasMore)return;
    const controller=new AbortController(),version=generation.current;moreRequest.current=controller;setLoadingMore(true);setMoreError('');
    try{
      const data=await request(offset,controller.signal);
      if(version!==generation.current)return;
      setMovies(items=>[...items,...data.recommendations.filter(movie=>!items.some(item=>item.movieId===movie.movieId))]);
      setOffset(data.nextOffset);setHasMore(data.hasMore);
    }catch(e){if(e.name!=='AbortError'&&version===generation.current)setMoreError('Could not load more films. Please try again.');}
    finally{if(moreRequest.current===controller){moreRequest.current=null;setLoadingMore(false);}}
  };
  const displayed=local?localMovies.slice(0,localCount):movies;
  const moreAvailable=local?localCount<localMovies.length:hasMore;
  return <section className="collection-page" aria-label={info.title}><a href="#/" className="back-link"><ArrowLeft size={15}/> Back to Home</a><div className="collection-page-heading"><div><div className="page-eyebrow">YOUR MOVIE COLLECTION</div><h1>{info.title}</h1><p className="page-intro">{info.description}</p></div>{!local&&<button className="filter-button" aria-expanded={showFilters} onClick={()=>setShowFilters(!showFilters)}><SlidersHorizontal size={15}/> Fine-tune</button>}</div>
    {showFilters&&!local&&<div className="filters">{route.concept!=='genre'&&<label>Genre<select aria-label="Genre" value={filterGenre} onChange={e=>setFilterGenre(e.target.value)}><option value="">All genres</option>{stats?.genres.map(genre=><option key={genre}>{genre}</option>)}</select></label>}<label>Release era<select aria-label="Release era" value={era} onChange={e=>setEra(e.target.value)}><option value="">Any era</option><option value="classic">Before 2000</option><option value="2000">2000–2009</option><option value="2010">2010 onward</option></select></label><label>Find films by<select aria-label="Find films by" value={mode} onChange={e=>setMode(e.target.value)}><option value="hybrid">Smart mix</option><option value="content">More like my picks</option><option value="collaborative">Audience patterns</option><option value="popular">Crowd favorites</option></select></label><label>More variety<input aria-label="Recommendation variety" type="range" min="0" max="0.5" step="0.05" value={diversity} onChange={e=>setDiversity(Number(e.target.value))}/></label><button onClick={()=>{setFilterGenre('');setEra('');setMode('hybrid');setDiversity(.15);}}>Reset</button></div>}
    {error&&<div className="error" role="alert"><span>{error}</span><button onClick={()=>setRetry(value=>value+1)}>Try again</button></div>}
    {busy?<div className="movie-grid" aria-label="Loading collection">{Array.from({length:6},(_,i)=><div className="skeleton" key={i}><div/><span/><span/></div>)}</div>:displayed.length?<div className="movie-grid collection-grid">{displayed.map(movie=><MovieCard key={movie.movieId} movie={movie} {...cardProps(movie)}/>)}</div>:!error&&<EmptyState title={local?'Nothing here yet.':'No films in this selection.'} href={route.concept==='watch-again'?'#/watched':'#/'} label={route.concept==='watch-again'?'Add watched movies':'Explore Home'}>{route.concept==='saved'?'Bookmark films to keep them here.':route.concept==='watch-again'?'Rate a watched movie 4 or 5 stars to find it here.':'Try a different era or filter.'}</EmptyState>}
    {!busy&&!error&&displayed.length>0&&<div className="see-more-section" aria-live="polite">{moreError&&<p role="alert">{moreError}</p>}{moreAvailable?<button className="see-more-button" disabled={loadingMore} onClick={loadMore}>{loadingMore?<LoaderCircle size={16} className="spin"/>:<Plus size={16}/>} {loadingMore?'Finding more films…':'Load more movies'}</button>:<p>You’ve reached the end of this collection.</p>}<small>{displayed.length} films shown</small></div>}
  </section>;
}

function EvaluationPage({report,stats}) {
  return <section className="lab"><div className="eyebrow">BEHIND THE RECOMMENDATIONS</div><h1>The screening room.</h1><p>Real experiments, measured on later MovieLens ratings.</p>{report?<><div className="lab-stats"><div><strong>{report.test.hybrid.evaluated_users}</strong><span>Eligible test viewers</span></div><div><strong>{report.k}</strong><span>Recommendations per viewer</span></div><div><strong>{stats?.movies.toLocaleString()}</strong><span>Movies in the candidate catalog</span></div></div><div className="table-wrap"><table><caption>Time-based evaluation · diversity off · higher is better</caption><thead><tr><th>Method</th><th>NDCG@{report.k}</th><th>Recall@{report.k}</th><th>Precision@{report.k}</th><th>Catalog coverage</th></tr></thead><tbody>{Object.entries(report.test).map(([name,result])=><tr key={name}><td>{name}</td><td>{result.ndcg.toFixed(4)}</td><td>{result.recall.toFixed(4)}</td><td>{result.precision.toFixed(4)}</td><td>{(100*result.catalog_coverage).toFixed(1)}%</td></tr>)}</tbody></table></div><details className="protocol" open><summary>What these results mean</summary><p>The earliest 70% of ratings fit the model, the next 15% select the blend, and the final 15% evaluate it after a refit on earlier ratings. Every unseen catalog movie is a candidate.</p><p>Test viewers need five earlier likes and at least one new movie rated 4 stars or higher. {report.test.hybrid.excluded_users} of {report.test.hybrid.heldout_users} test viewers do not meet this rule. Static catalog metadata does not reconstruct historical release availability.</p><p>The app uses a final model fitted on all ratings. Match signals are not confidence probabilities. Guest favorite genres and home shelves are not part of this historical benchmark.</p></details></>:<EmptyState title="No evaluation report yet.">Run the evaluation command in the README to create a measured report.</EmptyState>}</section>;
}

export default function App() {
  const [route,setRoute]=useState(readRoute);
  const [profile,setProfile]=useState(()=>stored('cinematch-profile').filter(movie=>Number.isFinite(movie.rating)&&movie.rating>=.5&&movie.rating<=5));
  const [watchlist,setWatchlist]=useState(()=>stored('cinematch-watchlist'));
  const [favorites,setFavorites]=useState(()=>{
    try{const value=JSON.parse(localStorage.getItem('cinematch-favorite-genres')||'[]');return Array.isArray(value)?[...new Set(value.filter(genre=>typeof genre==='string'&&genre.length<=40))].slice(0,5):[];}catch{return [];}
  });
  const [stats,setStats]=useState(null),[report,setReport]=useState(null);
  const [home,setHome]=useState(null),[busy,setBusy]=useState(true),[error,setError]=useState('');
  const [storageError,setStorageError]=useState(''),[notice,setNotice]=useState(''),[retry,setRetry]=useState(0);
  useEffect(()=>{const change=()=>{setRoute(readRoute());window.scrollTo({top:0,behavior:'instant'});};window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change);},[]);
  useEffect(()=>{try{localStorage.setItem('cinematch-profile',JSON.stringify(profile));localStorage.setItem('cinematch-watchlist',JSON.stringify(watchlist));localStorage.setItem('cinematch-favorite-genres',JSON.stringify(favorites));setStorageError('');}catch{setStorageError('Browser storage is unavailable. Your choices will last for this visit only.');}},[profile,watchlist,favorites]);
  useEffect(()=>{if(!notice)return;const timer=setTimeout(()=>setNotice(''),4500);return()=>clearTimeout(timer);},[notice]);
  useEffect(()=>{const controller=new AbortController();api('/stats',{signal:controller.signal}).then(setStats).catch(()=>{});api('/evaluation',{signal:controller.signal}).then(setReport).catch(()=>{});return()=>controller.abort();},[retry]);
  useEffect(()=>{const controller=new AbortController();setBusy(true);setError('');setHome(null);api('/home',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({ratings:ratingsFor(profile),favorite_genres:favorites})}).then(setHome).catch(e=>{if(e.name!=='AbortError')setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});return()=>controller.abort();},[profile,favorites,retry]);
  const addWatched=movie=>{if(profile.some(item=>item.movieId===movie.movieId))return;if(profile.length>=100){setNotice('Your history holds 100 movies. Remove a film on the Watched page to add another.');return;}setProfile(items=>[...items,{...movie,rating:5,watchedAt:Date.now()}]);setNotice(`${movie.title} added to Watched movies.`);};
  const toggleSave=movie=>setWatchlist(items=>items.some(item=>item.movieId===movie.movieId)?items.filter(item=>item.movieId!==movie.movieId):[movie,...items].slice(0,100));
  const toggleGenre=genre=>setFavorites(items=>items.includes(genre)?items.filter(item=>item!==genre):items.length<5?[...items,genre]:items);
  const demo=async()=>{try{const movies=await Promise.all([2571,79132,109487].map(id=>api(`/movies/${id}`)));setProfile(items=>[...items,...movies.filter(movie=>!items.some(item=>item.movieId===movie.movieId)).map(movie=>({...movie,rating:5,watchedAt:Date.now()}))].slice(0,100));}catch(e){setNotice(e.message);}};
  const cardProps=movie=>({saved:watchlist.some(item=>item.movieId===movie.movieId),picked:profile.some(item=>item.movieId===movie.movieId),onSave:toggleSave,onPick:addWatched,onManage:()=>{window.location.hash='/watched';}});
  const rewatches=useMemo(()=>watchAgain(profile),[profile]);
  const saved=watchlist.map(movie=>({...movie,reason:undefined}));
  const genreCaption=home?.genreSource==='favorites'?'From your favorite genres':home?.genreSource==='history'?'From your most-watched genres':'Explore the collection';
  return <div className="app-shell"><aside className="rail"><a href="#/" className="brand-mark" aria-label="CineMatch home">c<span>✦</span></a><nav className="rail-links" aria-label="Main navigation"><a className={route.page==='home'?'active':''} href="#/" aria-label="Home" title="Home"><Compass size={22}/></a><a className={route.page==='watched'?'active':''} href="#/watched" aria-label="Watched movies" title="Watched movies"><History size={21}/></a><a className={route.concept==='saved'?'active':''} href="#/collection/saved" aria-label="Saved movies" title="Saved movies"><Bookmark size={21}/><span className="rail-count">{watchlist.length||''}</span></a><a className={route.page==='genres'?'active':''} href="#/genres" aria-label="Favorite genres" title="Favorite genres"><Heart size={21}/></a><a className={route.page==='lab'?'active':''} href="#/lab" aria-label="Evaluation lab" title="Evaluation lab"><FlaskConical size={21}/></a></nav><div className="rail-bottom">CM<span>01 / 26</span></div></aside><div className="main-shell"><header><a href="#/" className="wordmark">cinematch<span>.</span></a><span className="header-note">A LITTLE LESS SCROLLING. A LOT MORE CINEMA.</span><a className="header-history" href="#/watched"><History size={14}/><span>Your watched movies</span></a><a className="taste-shortcut" href="#/genres"><Heart size={14}/><span>Your genres</span></a></header><main>
    {storageError&&<div className="error" role="alert">{storageError}</div>}
    {route.page==='home'&&<><section className="home-hero"><div><div className="eyebrow"><span className="live-dot"/> YOUR PERSONAL PICTURE HOUSE</div><h1>Your next favorite.<br/><em>Now showing.</em></h1><p>A few familiar favorites. A few unexpected discoveries.</p><a href="#/watched" className="text-link">Shape your recommendations<ArrowUpRight size={15}/></a></div><div className="home-hero-art" aria-label="Cinema clapperboard artwork"><ClapperboardArt/><span>LIGHTS. CAMERA. YOUR KIND OF CINEMA.</span></div></section>
      {error&&<div className="error" role="alert"><span>{error}</span><button onClick={()=>setRetry(value=>value+1)}>Try again</button></div>}
      {busy?<section className="home-loading" aria-label="Loading home rows"><LoaderCircle className="spin" size={20}/><p>Putting your movie night together…</p></section>:<Shelf title="Movies you might like" subtitle="Picked for your next movie night." movies={home?.recommendations||[]} href="#/collection/recommended" empty="Add watched movies or favorite genres to shape your picks." emptyHref="#/watched" emptyLabel="Add watched movies" cardProps={cardProps}/>}
      <Shelf title="Saved movies" subtitle={`${watchlist.length} ${watchlist.length===1?'film':'films'} kept for later.`} movies={saved} href="#/collection/saved" empty="Bookmark a movie to keep it for a future movie night." cardProps={cardProps}/>
      <Shelf title="Watch again" subtitle="The watched films you rated highest." movies={rewatches} href="#/collection/watch-again" empty="Add watched movies and rate your favorites to find them here." emptyHref="#/watched" emptyLabel="Go to Watched movies" cardProps={cardProps}/>
      {!busy&&home?.genres?.length>0&&<div className="genre-shelves-caption"><span>{genreCaption}</span><a href="#/genres">Choose genres<ArrowUpRight size={13}/></a></div>}
      {!busy&&home?.genres?.map(shelf=><Shelf key={shelf.genre} title={`${shelf.genre} movies`} subtitle={home.genreSource==='history'?`${shelf.watchedCount} watched ${shelf.watchedCount===1?'film':'films'} in this genre.`:home.genreSource==='favorites'?'Because you picked this genre.':'A genre to explore while your history gets started.'} movies={shelf.movies} href={genreHref(shelf.genre)} empty="You’ve seen all available films in this genre. Explore your watched movies or another collection." emptyHref="#/watched" emptyLabel="View watched movies" cardProps={cardProps}/>)}</>}
    {route.page==='watched'&&<WatchedPage profile={profile} onAdd={addWatched} onRate={(id,rating)=>setProfile(items=>items.map(movie=>movie.movieId===id?{...movie,rating}:movie))} onRemove={id=>setProfile(items=>items.filter(movie=>movie.movieId!==id))} onDemo={demo} stats={stats}/>}
    {route.page==='genres'&&<GenreSettings stats={stats} favorites={favorites} onToggle={toggleGenre} onClear={()=>setFavorites([])}/>}
    {route.page==='collection'&&<CollectionPage key={`${route.concept}:${route.genre||''}`} route={route} profile={profile} favorites={favorites} watchlist={watchlist} cardProps={cardProps} stats={stats}/>}
    {route.page==='lab'&&<EvaluationPage report={report} stats={stats}/>}
    {route.page==='not-found'&&<EmptyState title="This collection wasn’t found." href="#/" label="Back to Home">Choose a collection from your home page.</EmptyState>}
    <footer><div className="footer-brand">cinematch<span>✦</span><small>GOOD TASTE. GREAT CINEMA.</small></div><div>{stats?`${stats.movies.toLocaleString()} films · ${stats.users} viewers · MovieLens`:'MovieLens collection'}<small>Posters & summaries via Cinemeta / MetaHub.</small></div><a href="#/lab">Behind the matches<ChevronRight size={14}/></a></footer>
  </main>{notice&&<div className="notice" role="status"><Check size={16}/><span>{notice}</span><button aria-label="Dismiss notification" onClick={()=>setNotice('')}><X size={14}/></button></div>}</div></div>;
}
