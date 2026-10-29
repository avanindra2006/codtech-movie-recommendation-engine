import test from 'node:test';
import assert from 'node:assert/strict';
import {readRoute,watchAgain,collectionInfo} from '../src/library.js';

test('home, watched history, settings and collection links are refreshable routes',()=>{
  assert.deepEqual(readRoute(''),{page:'home'});
  assert.deepEqual(readRoute('#/watched'),{page:'watched'});
  assert.deepEqual(readRoute('#/genres'),{page:'genres'});
  for(const concept of ['recommended','saved','watch-again']){
    assert.deepEqual(readRoute(`#/collection/${concept}`),{page:'collection',concept});
  }
});

test('a genre See more link retains its exact collection',()=>{
  const route=readRoute('#/collection/genre/Sci-Fi');
  assert.deepEqual(route,{page:'collection',concept:'genre',genre:'Sci-Fi'});
  assert.equal(collectionInfo(route).title,'Sci-Fi movies');
  assert.equal(collectionInfo(readRoute('#/collection/saved')).title,'Saved movies');
  assert.equal(collectionInfo(readRoute('#/collection/watch-again')).title,'Watch again');
});

test('invalid or incomplete collection links have a useful error route',()=>{
  for(const hash of ['#/unknown','#/collection/genre/','#/collection/genre/%E0%A4%A']){
    assert.deepEqual(readRoute(hash),{page:'not-found'});
  }
});

test('Watch again includes high ratings, puts favorites first, and preserves history',()=>{
  const history=[{movieId:1,rating:2},{movieId:2,rating:4,watchedAt:10},
    {movieId:3,rating:5,watchedAt:1},{movieId:4,rating:4,watchedAt:20}];
  const before=JSON.stringify(history);
  assert.deepEqual(watchAgain(history).map(movie=>movie.movieId),[3,4,2]);
  assert.equal(JSON.stringify(history),before);
  assert.deepEqual(watchAgain([]),[]);
});
