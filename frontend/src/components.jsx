import React, { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, ArrowRight, Bookmark, Check, ChevronRight, Clapperboard, Compass, FlaskConical, Heart, LoaderCircle, Plus, Search, SlidersHorizontal, Sparkles, Star, X } from 'lucide-react';

function stored(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '[]');
    return Array.isArray(value) ? value.filter(v => Number.isInteger(v.movieId) && v.movieId > 0 && typeof v.title === 'string').slice(0, 100) : [];
  } catch { return []; }
}

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) {
    let message = `Could not connect (${response.status}). Please try again.`;
    try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail; } catch { /* Keep a useful fallback for non-JSON responses. */ }
    throw new Error(message);
  }
  return response.json();
}

const paletteNames = ['ink', 'coral', 'sage', 'violet', 'sand', 'blue'];

function ClapperboardArt() {
  return <div className="clapper-art" aria-hidden="true">
    <div className="clapper-arm"><span/></div>
    <div className="clapper-body">
      <div className="clapper-studio">CINEMATCH <span>PICTURE NO. 001</span></div>
      <small>PRODUCTION</small><strong>YOUR NEXT<br/>FAVORITE.</strong>
      <div className="clapper-take"><span><small>SCENE</small>MOVIE NIGHT</span><span><small>TAKE</small>01</span><b>▶</b></div>
      <div className="clapper-credit"><span>DIRECTED BY</span> YOUR GOOD TASTE</div>
    </div>
  </div>;
}

function TitleArt({ movie, small = false }) {
  const palette = paletteNames[movie.movieId % paletteNames.length];
  return <div className={`title-art ${palette} ${small ? 'small-art' : ''}`} aria-hidden="true">
    <div className="art-top"><span>CINEMATCH COLLECTION</span><span>↗</span></div>
    <ClapperboardArt/>
    <div className="art-bottom"><span>{movie.genres?.[0] || 'Cinema'}</span><span>{movie.year || '—'}</span></div>
  </div>;
}

function MoviePoster({ movie, thumbnail = false }) {
  const [loadedId, setLoadedId] = useState(null);
  const [failedId, setFailedId] = useState(null);
  // Track the image identity instead of resetting in an effect: cached images can load
  // before a passive effect runs when moving between discovery and the watchlist.
  const loaded = loadedId === movie.movieId;
  const failed = failedId === movie.movieId;
  return <div className={`movie-poster ${thumbnail ? 'poster-thumbnail' : ''} ${loaded ? 'poster-loaded' : ''}`}>
    {thumbnail ? <div className={`mini-art ${paletteNames[movie.movieId % 6]}`}><Clapperboard size={18}/></div> : <TitleArt movie={movie}/>}
    {!failed && <img src={`/api/movies/${movie.movieId}/poster`} alt={`Poster for ${movie.title}`} width="400" height="580" loading="lazy" decoding="async" referrerPolicy="no-referrer" onLoad={() => setLoadedId(movie.movieId)} onError={() => setFailedId(movie.movieId)}/>}
  </div>;
}

const synopsisRequests = new Map();

function MovieDescription({ movieId }) {
  const paragraph = useRef(null);
  const [result, setResult] = useState(null);
  useEffect(() => {
    let active = true;
    setResult(null);
    const load = () => {
      if (!synopsisRequests.has(movieId)) {
        synopsisRequests.set(movieId, api(`/movies/${movieId}/description`)
          .catch(() => ({description:null, available:false})));
      }
      synopsisRequests.get(movieId).then(data => {if (active) setResult(data);});
    };
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {load(); observer.disconnect();}
    }, {rootMargin:'200px'});
    observer.observe(paragraph.current);
    return () => {active=false; observer.disconnect();};
  }, [movieId]);
  return <p ref={paragraph} className={`movie-description ${result?.description ? '' : 'description-muted'}`} title={result?.description || undefined}>
    {result ? result.description || 'A synopsis is not available for this film.' : 'Loading the story…'}
  </p>;
}

function MovieCard({ movie, saved, onSave, onPick, picked, onManage }) {
  return <article className="movie-card" data-movie-id={movie.movieId}>
    <div className="poster-wrap"><MoviePoster movie={movie} />
      <button className={`save-button ${saved ? 'is-saved' : ''}`} onClick={() => onSave(movie)} aria-label={`${saved ? 'Remove' : 'Save'} ${movie.title} ${saved ? 'from' : 'to'} watchlist`}><Bookmark size={17} fill={saved ? 'currentColor' : 'none'} /></button>
    </div>
    <div className="movie-meta"><span>{movie.year || 'Year unknown'}</span><span><Star size={11} fill="currentColor" /> {movie.ratingCount ? movie.meanRating.toFixed(1) : 'Unrated'}</span></div>
    <h3 title={movie.title}>{movie.title.replace(/\s*\(\d{4}\)\s*$/, '')}</h3>
    <p className="genre-line">{movie.genres?.join(' · ') || 'Uncategorized'}</p>
    <MovieDescription movieId={movie.movieId}/>
    {movie.reason && <p className="reason"><Sparkles size={12} /><span>{movie.reason}</span></p>}
    <button className={`pick-button ${picked ? 'picked' : ''}`} onClick={() => picked ? onManage?.(movie) : onPick(movie)} disabled={picked && !onManage}><span>{picked ? 'Manage rating' : 'Mark watched'}</span>{picked ? <Check size={15} /> : <Plus size={15} />}</button>
  </article>;
}


export {api, stored, ClapperboardArt, MoviePoster, MovieCard};
