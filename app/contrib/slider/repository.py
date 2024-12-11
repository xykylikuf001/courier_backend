from typing import TYPE_CHECKING

from app.db.repository import CRUDBase

from .models import Slider, SliderTranslation

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class CRUDSlider(CRUDBase[Slider]):
    async def create_with_translation(
            self,
            async_db: "AsyncSession",
            obj_in: dict,
            lang: str,
    ):
        try:
            db_obj = self.model(
                is_active=obj_in.get('is_active'),
                host=obj_in.get('host'),
                path=obj_in.get('path'),
                sort_order=obj_in.get('sort_order'),
                file_id=obj_in.get("file_id")
            )
            async_db.add(db_obj)
            await async_db.flush()

            db_obj_tr = SliderTranslation(
                id=db_obj.id,
                title=obj_in.get('title'),
                caption=obj_in.get('caption'),
                locale=lang,
            )
            async_db.add(db_obj_tr)
            await async_db.commit()
            await async_db.refresh(db_obj)
            await async_db.refresh(db_obj_tr)
            db_obj.current_translation = db_obj_tr
            return db_obj
        except Exception as e:
            print(e)
            await async_db.rollback()
            raise e


class CRUDSliderTranslation(CRUDBase[SliderTranslation]):
    pass


slider_repo = CRUDSlider(Slider)
slider_tr_repo = CRUDSliderTranslation(SliderTranslation)
