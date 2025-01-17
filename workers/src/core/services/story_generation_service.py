from typing import Dict, Any, List
import json
from datetime import datetime
from src.core.models.story import Story
from src.core.models.story_framework import StoryFramework
from src.core.services.llm_service import LLMService
from src.core.services.s3_service import S3Service
from src.core.utils.logging_config import setup_logging
from src.worker.config import settings

logger = setup_logging("story_generation", "story_generation.log")

class StoryGenerationService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.s3 = S3Service()

    async def _generate_section(
        self,
        story_bible: Dict[str, Any],
        framework: StoryFramework,
        arc_index: int,
        beat_index: int,
        previous_content: str = "",
    ) -> str:
        """Generate a single story section based on framework beat"""
        arc = framework.arcs[arc_index]
        beat = arc.beats[beat_index]

        # Modify prompt based on whether this is the first section
        is_first_section = arc_index == 0 and beat_index == 0
        
        # Pre-format the conditional parts to avoid complex f-string
        section_type = "opening section" if is_first_section else "next section"
        story_style = "opening" if is_first_section else "continuation"
        story_goal = "sets up the story" if is_first_section else "maintains flow and consistency with what came before"
        previous_content_section = "" if is_first_section else f"Previous Story Content:\n{previous_content}"
        
        prompt = f"""Write the {section_type} of the story. Do not include any meta-commentary or section headers.
        Write in a clear narrative style, starting directly with the story content.

        Current Arc: {arc.name}
        Current Beat: {beat.name}
        Description: {beat.description}
        Location: {beat.location}
        Characters: {', '.join(beat.characters_involved)}
        
        {previous_content_section}

        Write a vivid, engaging {story_style} that {story_goal}. Start directly with the narrative."""

        response = await self.llm.generate(
            prompt=prompt,
            temperature=settings.STORY_TEMPERATURE,
            max_tokens=settings.SECTION_MAX_TOKENS
        )
        
        # Clean up any meta-text from the response
        response = response.replace("Here's an opening for this story beat:", "")
        response = response.replace("Here's the next section:", "")
        response = response.replace("Here's a continuation of the scene:", "")
        response = response.replace("Here's the next section of the story:", "")
        response = response.split("---")[-1].strip()  # Remove any headers
        
        # Remove excessive newlines
        response = "\n\n".join(line.strip() for line in response.split("\n") if line.strip())
        
        logger.info(f"Generated section for {beat.name} ({len(response.split())} words)")
        return response

    async def generate_story(
        self,
        story_bible: Dict[str, Any],
        framework: StoryFramework
    ) -> Story:
        """Generate complete story through sequential section generation"""
        try:
            logger.info(f"Generating story: {framework.title}")
            
            full_content = []
            
            # Generate each section based on framework beats
            for arc_idx, arc in enumerate(framework.arcs):
                for beat_idx, beat in enumerate(arc.beats):
                    section = await self._generate_section(
                        story_bible=story_bible,
                        framework=framework,
                        arc_index=arc_idx,
                        beat_index=beat_idx,
                        previous_content="\n\n".join(full_content) if full_content else ""
                    )
                    full_content.append(section)
                    
                    logger.info(f"Generated section for {arc.name} - {beat.name}")

            # Combine all sections
            complete_story = "\n\n".join(full_content)
            
            # Create and save story
            story = Story(
                title=framework.title,
                genre=framework.genre,
                content=complete_story,
                word_count=len(complete_story.split()),
                framework_id=framework.title,
                bible_id=story_bible.get("title", ""),
                created=datetime.now(),
                file_paths=None
            )
            
            story_urls = await self._save_story(story)
            story.file_paths = story_urls
            
            logger.info(f"Successfully generated complete story of {story.word_count} words")
            return story

        except Exception as e:
            logger.error(f"Error generating story: {str(e)}")
            raise 

    async def _save_story(self, story: Story) -> str:
        """Save story content as markdown with front matter"""
        try:
            # Create markdown content
            md_content = f"""---
title: {story.title}
genre: {story.genre}
author: {story.author}
created: {story.created.isoformat()}
word_count: {story.word_count}
framework: {story.framework_id}
bible: {story.bible_id}
---

# {story.title}

{story.content}
"""
            # Save markdown version
            md_url = await self.s3.save_story(
                content=md_content,
                story_id=story.title.lower().replace(' ', '_'),
                story_type='story',
                format='md'
            )
            
            # Save plain text version (just the content)
            txt_url = await self.s3.save_story(
                content=story.content,
                story_id=story.title.lower().replace(' ', '_'),
                story_type='story',
                format='txt'
            )
            
            # Save JSON version
            json_content = {
                "title": story.title,
                "genre": story.genre,
                "author": story.author,
                "created": story.created.isoformat(),
                "word_count": story.word_count,
                "framework_id": story.framework_id,
                "bible_id": story.bible_id,
                "content": story.content
            }
            json_url = await self.s3.save_story(
                content=json.dumps(json_content, indent=2),
                story_id=story.title.lower().replace(' ', '_'),
                story_type='story',
                format='json'
            )
            
            # Return all URLs in the result
            return {
                "markdown_url": md_url,
                "text_url": txt_url,
                "json_url": json_url
            }
            
        except Exception as e:
            logger.error(f"Error saving story to S3: {str(e)}")
            raise 