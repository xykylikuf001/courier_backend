from typing import TYPE_CHECKING

from app.db.repository import CRUDBase, CRUDBaseSync, prepare_data_with_slug

from .models import Place, PlaceTranslation

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class CRUDPlaceSync(CRUDBaseSync[Place]):
    pass


class CRUDPlaceTranslationSync(CRUDBaseSync[PlaceTranslation]):
    pass


class CRUDPlace(CRUDBase[Place]):
    async def create_with_translation(
            self,
            async_db: "AsyncSession",
            obj_in: dict,
            lang: str,
    ):
        name = obj_in.get("name")
        prepared = await prepare_data_with_slug(
            async_db=async_db,
            obj_in={"slug": obj_in.get('slug'), "name": name},
            obj_repo=self,
            from_field="name",
        )

        try:
            db_obj = self.model(
                slug=prepared.get("slug"),
                parent_id=obj_in.get("parent_id"),
                location_level=obj_in.get("location_level"),
                is_active=obj_in.get("is_active")
            )

            async_db.add(db_obj)
            await async_db.flush()

            db_obj_tr = PlaceTranslation(
                id=db_obj.id,
                name=name,
                full_name=obj_in.get('full_name'),
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


class CRUDPlaceTranslation(CRUDBase[PlaceTranslation]):
    pass


place_translation_repo = CRUDPlaceTranslation(PlaceTranslation)
place_repo = CRUDPlace(Place)
place_repo_sync = CRUDPlaceSync(Place)
place_translation_repo_sync = CRUDPlaceTranslationSync(PlaceTranslation)
