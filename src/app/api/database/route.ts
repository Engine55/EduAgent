import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(request: NextRequest) {
  try {
    const { action, data } = await request.json()

    switch (action) {
      case 'save_requirement':
        const requirement = await prisma.eduData.create({
          data: {
            id: data.id,
            dataType: 'requirement',
            userId: data.user_id,
            data: data.requirement_data,
          },
        })
        return NextResponse.json({ 
          success: true, 
          requirement_id: requirement.id,
          created_at: requirement.createdAt 
        })

      case 'get_requirement':
        const req = await prisma.eduData.findUnique({
          where: { id: data.requirement_id },
        })
        if (req) {
          return NextResponse.json({ success: true, data: req.data })
        } else {
          return NextResponse.json({ success: false, error: 'Requirement not found' })
        }

      case 'get_latest_requirement':
        const latest = await prisma.eduData.findFirst({
          where: { 
            dataType: 'requirement',
            ...(data.user_id && { userId: data.user_id })
          },
          orderBy: { createdAt: 'desc' },
        })
        if (latest) {
          return NextResponse.json({ 
            success: true, 
            data: latest.data,
            requirement_id: latest.id 
          })
        } else {
          return NextResponse.json({ success: false, error: 'No requirements found' })
        }

      case 'save_story':
        const story = await prisma.eduData.create({
          data: {
            id: data.story_id,
            dataType: 'story',
            userId: null,
            data: { ...data.story_data, requirement_id: data.requirement_id },
          },
        })
        return NextResponse.json({ 
          success: true, 
          story_id: story.id,
          created_at: story.createdAt 
        })

      case 'save_storyboard':
        const storyboard = await prisma.eduData.create({
          data: {
            id: data.storyboard_id,
            dataType: 'storyboard',
            userId: null,
            data: { ...data.storyboard_data, story_id: data.story_id },
          },
        })
        return NextResponse.json({ 
          success: true, 
          storyboard_id: storyboard.id,
          created_at: storyboard.createdAt 
        })

      default:
        return NextResponse.json({ success: false, error: 'Unknown action' })
    }
  } catch (error) {
    console.error('Database API error:', error)
    return NextResponse.json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    })
  }
}